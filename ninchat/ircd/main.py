# Copyright (c) 2013, Somia Reality Oy
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from __future__ import absolute_import

import json
import socket

import gevent
import gevent.queue

from ninchat.client.call import SyncQueueAdapter
from ninchat.client.gevent import QueueSession

from . import log

command_handlers = {}

class Client(object):

	def __init__(self, to_irc):
		self.to_irc = to_irc
		self.user_id = None
		self.user_auth = None
		self.name = None
		self.session = None

	@property
	def ident(self):
		return "%s!%s@ninchat".format(self.name, self.user_id)

	def send_to_irc(self, line):
		self.to_irc.put(line.encode("utf-8"))

	def set_name(self, name):
		if self.name is None:
			self.name = name
		else:
			self.session.update_user("")

	def init_auth(self, user_auth):
		if self.user_auth is not None:
			log.error("user_id and/or user_auth already set")
			return

		self.user_auth = user_auth

	def init_session(self, user_id, realname):
		if self.user_id is not None:
			log.error("user_id already set")
			return

		self.user_id = user_id

		session = SyncQueueAdapter(QueueSession())
		gevent.spawn(self._receive, session)

		event = session.create(
				message_types = ["ninchat.com/*"],
				user_id       = self.user_id,
				user_auth     = self.user_auth,
				user_attrs    = {
					"name":     self.name,
					"realname": realname,
				})

		if event.name == "error":
			log.error("error: %r", event)
			return

		self.name = event.user_attrs.get("name")
		self.session = session

		self.send_to_irc(":{} NICK :{}".format(self.ident, self.name))
		self.send_to_irc(":ninchat 020 * :Ninchat IRC adapter")

	def _receive(self, session):
		while True:
			event = session.receive_event()
			if event is None:
				break

			log.debug("event: %r", event)

			if event.name == "message_received" and event.message_type == "ninchat.com/text":
				self.send_to_irc(":{}!{}@ninchat PRIVMSG {} {}".format(
						event.message_user_name or event.message_user_id,
						event.message_user_id,
						self.name,
						json.loads(event.payload[0])["text"]))

class Command(object):

	def __init__(self, raw):
		self.raw = raw

	def __str__(self):
		return repr(self.raw)

	def parse(self):
		line = self.raw.decode("utf-8")

		if line.startswith(":"):
			parts = line.split(" ", 2)
			self.prefix = parts[0]
		else:
			parts = line.split(" ", 1)
			self.prefix = None

		self.name = parts[-2]
		self.params = parts[-1]

def main():
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind(("127.0.0.1", 6667))
	sock.listen(socket.SOMAXCONN)

	while True:
		gevent.spawn(handle_client, sock.accept())

def handle_client((conn, addr)):
	host, _ = addr
	log.info("connection from %s", host)

	commands = gevent.queue.Queue()
	gevent.spawn(read_commands, conn, commands)

	to_irc = gevent.queue.Queue()
	gevent.spawn(write_to_irc, conn, to_irc)

	client = Client(to_irc)

	try:
		while True:
			command = commands.get()
			if command is None:
				break

			try:
				command.parse()
			except:
				log.exception("failed to parse command: %s", command)
				continue

			handler = command_handlers.get(command.name)
			if handler is None:
				log.warning("unknown command: %s", command)
				continue

			handler(client, command.params)

		log.info("disconnect from %s", host)
	finally:
		to_irc.put(None)

def read_commands(conn, queue):
	try:
		buf = b""

		while True:
			data = conn.recv(512)
			if not data:
				break

			buf += data

			while True:
				i = buf.find(b"\r\n")
				if i < 0:
					break

				queue.put(Command(buf[:i]))
				buf = buf[i+2:]
	finally:
		queue.put(None)

def write_to_irc(conn, queue):
	while True:
		line = queue.get()
		if line is None:
			break

		conn.send(line)
		conn.send(b"\r\n")

def handle_command(name):
	def decorator(func):
		command_handlers[name] = func

	return decorator

@handle_command("PASS")
def _(client, params):
	client.init_auth(params)

@handle_command("NICK")
def _(client, params):
	client.set_name(params)

@handle_command("USER")
def _(client, params):
	user_id, _, _, realname = params.split(" ", 3)
	client.init_session(user_id, realname)
