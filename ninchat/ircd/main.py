# Copyright (c) 2013-2014, Somia Reality Oy
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

from __future__ import absolute_import, unicode_literals

import json
import socket
import time

import gevent
import gevent.queue

from ..client.adapter import SyncQueueAdapter
from ..client.session.gevent import QueueSession

from . import log

SERVER = "ninchat"

def async(func):
	def spawner(*args, **kwargs):
		gevent.spawn(func, *args, **kwargs)
	return spawner

class Queue(gevent.queue.Queue):

	def __iter__(self):
		return self

	def next(self):
		while True:
			return self.get()

class TerminatedQueue(gevent.queue.Queue):

	class Termination(object):

		def __init__(self, queue):
			self.queue = queue

		def __enter__(self):
			return self.queue

		def __exit__(self, *exc):
			self.queue.put(None)

	def __init__(self, maxsize=0, terminators=1):
		super(TerminatedQueue, self).__init__(max(maxsize, terminators))
		self.__terminators = terminators

	def __iter__(self):
		return self

	def next(self):
		while True:
			item = self.get()
			if item is None:
				self.__terminators -= 1
				if self.__terminators <= 0:
					raise StopIteration
			else:
				return item

	def termination(self):
		return self.Termination(self)

class User(object):

	def __init__(self, client, client_send_queue):
		self.client = client
		self.client_send_queue = client_send_queue
		self.user_id = None
		self.user_auth = None
		self.user_name = None
		self.session = None
		self.search_queues = {}
		self.channels_attrs = {}

	def __str__(self):
		if self.user_id is not None:
			return "user {}!{}".format(self.user_name, self.user_id)
		elif self.user_name is not None:
			return "user {}?".format(self.user_name)
		else:
			return "user unknown"

	@property
	def ident(self):
		return "{}^{}!{}".format(self.user_name, self.user_id, SERVER)

	def log_call_error(self, action, event):
		if event.error_reason:
			log.error("%s %s error: %s (%s)", self, action, event.error_type, event.error_reason)
		else:
			log.error("%s %s error: %s", self, action, event.error_type)

	def send(self, line):
		self.client_send_queue.put(line.encode("utf-8"))

	def set_auth(self, user_auth):
		if self.user_auth is None:
			self.user_auth = user_auth
		else:
			log.error("%s resent PASS command", self)
			self.client.disconnect = True

	def set_name(self, name):
		if "^" in name:
			name, _ = name.split("^", 1)

		if self.user_name is None:
			self.user_name = name
		else:
			self._update_name(name)

	@async
	def _update_name(self, name):
		event = self.session.update_user(user_attrs={ "name": name })
		if event.name == "error":
			self.log_call_error("update_user", event)
		else:
			self.user_name = event.user_attrs.get("name", "")
			self.send(":{} NICK :{}^{}".format(self.ident, self.user_name, self.user_id))

	def init(self, user_id, realname):
		if self.user_id is not None:
			log.error("%s resent USER command", self)
			self.client.disconnect = True
			return

		self.user_id = user_id

		session = SyncQueueAdapter(QueueSession())
		self._session_recv_loop(session)

		try:
			event = session.create(
					message_types = ["ninchat.com/*"],
					user_id       = self.user_id,
					user_auth     = self.user_auth,
					user_attrs    = {
						"name":     self.user_name,
						"realname": realname,
					})

			if event.name == "error":
				self.log_call_error("create_session", event)
				self.client.disconnect = True
			else:
				self.user_name = event.user_attrs["name"]
				self.session = session

				log.info("%s is %s", self.client, self)

				self.send(":{} NICK :{}^{}".format(self.ident, self.user_name, self.user_id))
				self.send(":{} 001 {}^{} :Welcome to Ninchat".format(SERVER, self.user_name, self.user_id))
				for channel_id, channel_info in event.user_channels.iteritems():
					self.channels_attrs[channel_id] = channel_info["channel_attrs"]
					self._joined(channel_id, channel_info["channel_attrs"])
		finally:
			if self.session is not session:
				session.close()

	@async
	def _session_recv_loop(self, session):
		for event in session:
			log.debug("%s received %s event", self, event)

			if event.name == "user_updated":
				if event.user_id == self.user_id:
					name = event.user_attrs.get("name", "")
					if name != self.user_name:
						self.user_name = name
						self.send(":{} NICK :{}^{}".format(self.ident, self.user_name, self.user_id))
			elif event.name == "message_received":
				if event.message_type == "ninchat.com/text":
					text = json.loads(event.payload[0])["text"]

					if event.channel_id is not None:
						self.send(":{}^{}!{} PRIVMSG #{} :{}".format(
								event.message_user_name or "",
								event.message_user_id,
								SERVER,
								event.channel_id,
								text))
					elif event.user_id is not None:
						self.send(":{}^{}!{} PRIVMSG {}^{} :{}".format(
								event.message_user_name or "",
								event.message_user_id,
								SERVER,
								self.user_name,
								self.user_id,
								text))
			elif event.name == "search_results":
				queue = self.search_queues.get(event.action_id)
				if queue:
					queue.put(event)
				else:
					log.error("%s received search_results event for unknown search %s", self, event.action_id)

	@async
	def send_channel(self, channel_id, text):
		event = self._send_message(text, channel_id=channel_id)
		if event.name == "error":
			self.log_call_error("send_message channel %s" % channel_id, event)

	@async
	def send_user(self, target, text):
		_, user_id = target.split("^", 1)
		event = self._send_message(text, user_id=user_id)
		if event.name == "error":
			self.log_call_error("send_message user %s" % user_id, event)

	def _send_message(self, text, **params):
		return self.session.send_message(
				message_type = "ninchat.com/text",
				payload      = [json.dumps({ "text": text }).encode("utf-8")],
				**params)

	def join(self, channel_id):
		channel_attrs = self.channels_attrs.get(channel_id)
		if channel_attrs is None:
			event = self.session.join_channel(channel_id=channel_id)
			if event.name == "error":
				self.log_call_error("join_channel", event)
				return

			self.channels_attrs[channel_id] = event.channel_attrs
			channel_attrs = event.channel_attrs

		self._joined(channel_id, channel_attrs)
		self._names(channel_id)

	def _joined(self, channel_id, channel_attrs):
		self.send(":{} JOIN #{}".format(
				self.ident,
				channel_id))
		self.send(":{} 332 * #{} :{}: {}".format(
				SERVER,
				channel_id,
				channel_attrs.get("name", ""),
				channel_attrs.get("topic", "")))

	def _names(self, channel_id):
		event = self.session.describe_channel(channel_id=channel_id)
		if event.name == "error":
			self.log_call_error("describe_channel %s" % channel_id, event)
		else:
			self.send(":{} 353 * #{} :{}".format(
					SERVER,
					channel_id,
					" ".join(
						"{}^{}".format(info["user_attrs"].get("name", ""), id)
						for id, info
						in (event.channel_members or {}).iteritems()
					)))

			self.send(":{} 366 * #{} :End of NAMES list".format(
					SERVER,
					channel_id))

	@async
	def ping(self):
		event = self.session.ping()
		if event.name == "error":
			self.log_call_error("ping", event)
		else:
			self.send(":{} PONG %s".format(SERVER, SERVER))

	@async
	def whois(self, param):
		if "^" in param:
			_, user_id = param.split("^", 1)
			event = self.__describe_user(user_id)
			if event:
				self._send_whois_reply(event.user_id, event.user_attrs)
		else:
			param = param.lower()
			queue = TerminatedQueue(terminators=2)

			self._describe_user(param, queue)
			self._search(param, queue)

			for item in queue:
				if event.name == "user_found":
					self._send_whois_reply(event.user_id, event.user_attrs)
				elif event.name == "search_results":
					for user_id, user_attrs in event.users.iteritems():
						if user_attrs.get("name", "").lower() == param:
							self._send_whois_reply(user_id, user_attrs)

		self.send(":{} 318 {} :End of WHOIS list".format(SERVER, param))

	def _send_whois_reply(self, user_id, user_attrs):
		self.send(":{} 311 {}^{} {} {} * :{}".format(
				SERVER,
				user_attrs.get("name", ""),
				user_id,
				user_id,
				SERVER,
				user_attrs.get("realname", "")))

		idle_since = user_attrs.get("idle")
		if idle_since:
			self.send(":{} 317 {}^{} {} :seconds idle".format(
					SERVER,
					user_attrs.get("name", ""),
					user_id,
					int(time.time() - idle_since)))

	@async
	def _describe_user(self, user_id, result_queue):
		with result_queue.termination():
			event = self.__describe_user(user_id)
			if event:
				result_queue.put(event)

	def __describe_user(self, user_id):
		event = self.session.describe_user(user_id=user_id)
		if event.name == "error":
			if event.error_type != "user_not_found":
				self.log_call_error("describe_user %r" % user_id, event)
		else:
			return event

	@async
	def _search(self, name, result_queue):
		with result_queue.termination():
			action_id = self.session.new_action_id()
			search_queue = TerminatedQueue()

			self.search_queues[action_id] = search_queue

			try:
				log.debug("%s search %s began", self, action_id)

				event = self.session.search(action_id=action_id, search_term=name)
				if event.name == "error":
					self.log_call_error("search %r" % name, event)
				else:
					for event in search_queue:
						if event.users:
							result_queue.put(event)
						elif event.channels:
							pass
						else:
							break
			finally:
				del self.search_queues[action_id]

				log.debug("%s search %s ended", self, action_id)

	def close(self):
		if self.session:
			self.session.close()

class Client(object):

	class Commands(dict):
		handlers = {}

		@classmethod
		def handle(cls, name):
			def decorator(func):
				assert name not in cls.handlers
				cls.handlers[name] = func
			return decorator

	def __init__(self, (conn, addr)):
		self.conn = conn
		self.addr = addr
		self.disconnect = False

		self._main_loop()

	def __str__(self):
		return "client {}:{}".format(*self.addr)

	@async
	def _main_loop(self):
		log.info("%s connection", self)

		try:
			recv_queue = TerminatedQueue()
			send_queue = TerminatedQueue()
			close_queue = TerminatedQueue(terminators=2)

			self._recv_loop(recv_queue, close_queue)
			self._send_loop(send_queue, close_queue)

			user = User(self, send_queue)

			try:
				with send_queue.termination():
					for line in recv_queue:
						if self.disconnect:
							break

						try:
							line = line.decode("utf-8")
							if line.startswith(":"):
								parts = line.split(" ", 2)
							else:
								parts = line.split(" ", 1)
							command = parts[-2]
							params = parts[-1]
						except:
							log.exception("%s command parse error: %r", self, line)
							continue

						handler = self.Commands.handlers.get(command)
						if handler is None:
							log.warning("%s command unknown: %r", self, line)
							continue

						handler(self, user, params)
			finally:
				user.close()

			for _ in close_queue:
				pass
		finally:
			log.info("%s disconnecting %s", self, user)
			self.conn.close()

	@async
	def _recv_loop(self, recv_queue, close_queue):
		with close_queue.termination(), recv_queue.termination():
			buf = b""

			while not self.disconnect:
				data = self.conn.recv(512)
				if not data:
					break

				buf += data

				while True:
					i = buf.find(b"\r\n")
					if i < 0:
						break

					recv_queue.put(buf[:i])
					buf = buf[i+2:]

	@async
	def _send_loop(self, send_queue, close_queue):
		with close_queue.termination():
			for line in send_queue:
				self.conn.send(line + b"\r\n")

	@Commands.handle("PASS")
	def _(self, user, params):
		user.set_auth(params)

	@Commands.handle("NICK")
	def _(self, user, params):
		user.set_name(params)

	@Commands.handle("USER")
	def _(self, user, params):
		user_id, _, _, realname = params.split(" ", 3)
		user.init(user_id, realname)

	@Commands.handle("MODE")
	def _(self, user, params):
		pass

	@Commands.handle("PING")
	def _(self, user, params):
		if " " not in params and params == SERVER:
			user.ping()
		else:
			log.warning("%s %s sent unsupported PING parameters: %s", self, user, params)

	@Commands.handle("PRIVMSG")
	def _(self, user, params):
		target, text = params.split(" ", 1)
		text = text[1:]
		if target[0] == "#":
			user.send_channel(target[1:], text)
		else:
			user.send_user(target, text)

	@Commands.handle("JOIN")
	def _(self, user, params):
		self._join(user, params)

	@async
	def _join(self, user, params):
		for channel in params.split(","):
			user.join(channel[1:])

	@Commands.handle("WHOIS")
	def _(self, user, params):
		if " " in params:
			params, _ = params.split(" ", 1)

		user.whois(params)

	@Commands.handle("QUIT")
	def _(self, user, params):
		self.disconnect = True

def main():
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind(("127.0.0.1", 6667))
	sock.listen(socket.SOMAXCONN)

	while True:
		Client(sock.accept())
