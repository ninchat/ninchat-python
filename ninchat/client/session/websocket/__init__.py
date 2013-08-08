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

from __future__ import absolute_import

import time

from ... import log
from ...action import Action, SessionAction
from .. import SessionBase

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
		if self.session._handle_receive(event):
			self.session._received_callback(self.session, event)

	def _closed(self):
		if self.session._handle_disconnect():
			self.session._closed_callback(self.session)

class QueueConnectionBase(ConnectionBase):

	def _received(self, event):
		if self.session._handle_receive(event):
			self.session.event_queue.put(event)

	def _closed(self):
		if self.session._handle_disconnect():
			self.session.event_queue.put(None)

class TransportSessionBase(SessionBase):
	TERMINATE = object()

	def __init__(self):
		super(TransportSessionBase, self).__init__()
		self._init = self._flag_type()
		self._reset = False
		self._closing = False

	def _handle_send(self, action):
		pass

	def _handle_receive(self, event):
		caller_handles = True

		if not self._init.is_set():
			if event.type == "session_created":
				self.session_id = event._params.pop("session_id")
				self.session_host = event._params.pop("session_host")
			elif event.type == "error":
				if event.error_type == "session_not_found" and self.session_id is not None:
					self.__reset_session()
					caller_handles = False
				else:
					self.__terminate()
			else:
				log.error("unexpected reply to create_session from server: %s", event)
				self.__reset_session()
				caller_handles = False
			self._init.set()
		elif event.type == "error":
			if event.error_type == "session_not_found":
				self.__reset_session()
				caller_handles = False

		try:
			event_id = event._params.pop("event_id")
			if event_id is not None:
				self._event_id = event_id
		except KeyError:
			pass

		return caller_handles

	def __reset_session(self):
		self.session_id = None
		self._reset = True
		self.action_queue.put(None)

	def __terminate(self):
		self._closing = True
		self._reset = True
		self.action_queue.put(None)

	def _handle_disconnect(self):
		self._init.set()

		if self._closing:
			self.action_queue.put(self.TERMINATE)
			return True
		else:
			self._reset = True
			self.action_queue.put(None)
			return False

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

				if self._reset:
					self._reset = False
					break

				if next_action is None:
					continue
				elif next_action is self.CLOSE_SESSION:
					next_action = SessionAction("close_session")
					self._closing = True
				elif next_action is self.TERMINATE:
					break

				if next_action._transient_for_session_id is not None and next_action._transient_for_session_id != self.session_id:
					log.debug("skipping transient %s", next_action)
					next_action = None
					continue

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
			conn = self._connection_type(self.session_host, self)

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
