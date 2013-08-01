# Copyright (c) 2012-2013, Somia Reality Oy
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

import time

from ninchat.client import log
from ninchat.client.action import Action, SessionAction
from ninchat.client.session import SessionBase

class ConnectionBase(object):
	url_format = "wss://{}/socket"
	protocols = ["ninchat.com-1"]

	def __init__(self, hostname, session):
		super(ConnectionBase, self).__init__(self.url_format.format(hostname), self.protocols)
		self.session = session

	def send_action(self, action):
		for frame in action._frames:
			self.send(frame)

class CallbackConnectionBase(ConnectionBase):

	def _received(self, event):
		self.session._handle_receive(event)
		self.session.received(event)

	def _closed(self):
		if self.session._handle_disconnect():
			self.session.closed()

class QueueConnectionBase(ConnectionBase):

	def _received(self, event):
		self.session._handle_receive(event)
		self.session.event_queue.put(event)

	def _closed(self):
		if self.session._handle_disconnect():
			self.session.event_queue.put(None)

class TransportSessionBase(SessionBase):

	def __init__(self):
		super(TransportSessionBase, self).__init__()
		self._reconnect = False
		self._closing = False

	def _send_loop(self):
		conn = None
		next_action = None
		last_event_id = None

		while True:
			if conn:
				try:
					conn.close()
				except:
					log.exception("websocket close")

				conn.close_connection()

			if self._closing:
				break

			if self.session_id is None:
				self.session_host = self.__class__.session_host
				self._init.clear()
				conn = self._connect(Action("create_session", **self.create_params))
				self._init.wait()

				if self.session_id is None:
					# TODO: something better
					time.sleep(1)
					continue
			else:
				last_event_id = self._event_id
				conn = self._connect(SessionAction("resume_session", self.session_id, last_event_id))

			while True:
				if next_action is None:
					next_action = self.action_queue.get()

				if self._reconnect:
					self._reconnect = False
					break

				if next_action is None:
					continue
				elif next_action is self.CLOSE_SESSION:
					next_action = SessionAction("close_session")
					self._closing = True
				elif next_action is self.SESSION_CLOSED:
					break

				next_event_id = self._event_id
				if next_event_id == last_event_id:
					next_event_id = None

				next_action._set_event_id(next_event_id)

				try:
					self._send(conn, next_action)
				except:
					log.exception("websocket send")
					break

				next_action = None

				if next_event_id is not None:
					last_event_id = next_event_id

	def _connect(self, action):
		while True:
			conn = self.connection_type(self.session_host, self)

			try:
				conn.connect()
			except:
				log.exception("websocket connect")
				conn.close_connection()
				# TODO: exponential backoff, eventually reset session_host
				time.sleep(1)
				continue

			try:
				self._send(conn, action)
			except:
				log.exception("websocket send")
				conn.close_connection()
				continue

			return conn

	def _send(self, conn, action):
		self._handle_send(action)
		conn.send_action(action)
