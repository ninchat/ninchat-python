# Copyright (c) 2012-2014, Somia Reality Oy
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

import bisect
import time

try:
	# Python 2
	import Queue as queue
except ImportError:
	# Python 3
	import queue

from ... import api

from .. import log
from ..action import Action, SessionAction

class ConnectionBase(object):
	protocols = ["ninchat.com"]

	def __init__(self, url, session):
		super(ConnectionBase, self).__init__(url, self.protocols)
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

class Pending(object):

	def __init__(self, critical_type):
		self.critical = critical_type()
		self.list = []
		self.map = {}

	def get(self):
		"""Get an action which should be resent now (or None) and the time
		after which one might be available for resending (or None).
		"""
		with self.critical:
			if not self.list:
				return None, None

			action = self.list[0]

		timeout = action._resend_time - time.time()
		if timeout > 0:
			return None, timeout
		else:
			return action, None

	def sent(self, action):
		"""An action was just (re)sent.
		"""
		if action.action_id is None:
			return

		with self.critical:
			if self.list and action is self.list[0]:
				del self.list[0]
				new = False
			else:
				new = True

			if action._sent():
				bisect.insort_left(self.list, action)
				if new:
					self.map[action.action_id] = action
			elif not new:
				del self.map[action.action_id]

	def drop(self, action):
		"""An action up for (re)sending is obsolete.
		"""
		if action.action_id is None:
			return

		with self.critical:
			if self.list and action is self.list[0]:
				del self.list[0]
				del self.map[action.action_id]

	def ack(self, event):
		"""An event was received.
		"""
		action_id = event._params.get("action_id")
		if action_id is None:
			return

		with self.critical:
			action = self.map.get(action_id)
			if action is not None:
				i = bisect.bisect_left(self.list, action)
				assert self.list[i] is action

				del self.list[i]
				del self.map[action_id]

class SessionBase(object):
	"""Actions may be sent via the send_action() method, the action_queue or by
	calling corresponding instance methods with keyword parameters;
	e.g. session.describe_user(user_id="0h6si071").

	A server session must be established by calling the create method and
	waiting for a "session_created" (or an "error") event.  If the server drops
	the session (due to network timeout or some other exceptional reason), a
	new server session is created automatically, and another "session_created"
	event is delivered.

	The context manager protocol is supported: the session is closed in a
	blocking manner after the with-suite.

	.. attribute:: action_queue

	   Queue for sending Action objects.

	"""
	CLOSE_SESSION = object()
	TERMINATE = object()

	session_host = "api.ninchat.com"
	url_format = "wss://{}/v2/socket"

	def __init__(self):
		self.action_queue = self.queue_type()
		self.session_id = None
		self._action_id = self._critical_type(0)
		self._event_id = None
		self._sender = self._executor_type(self._send_loop)
		self.__started = False
		self.__closed = False

		self._pending = Pending(self._critical_type)
		self._init = self._flag_type()
		self._reset = False
		self._closing = False

	def __enter__(self):
		return self

	def __exit__(self, *exc):
		if self.__started:
			self.close()
			self._sender.join()

	def __getattr__(self, name):
		if name not in api.actions:
			raise AttributeError(name)

		def call(**params):
			return self.send_action(name, **params)

		return call

	def create(self, **params):
		self.create_params = params
		self.__started = True
		self._sender.start()

	def new_action_id(self):
		with self._action_id as critical:
			critical.value += 1
			return critical.value

	def new_action(self, name, transient=False, **params):
		"""Create an Action, to be sent later.  The action_id parameter is
		generated implicitly (if applicable) unless specified by the caller.
		If transient is set, the action is relevant only during the current
		server session; it will not be retried if the session needs to be
		recreated.
		"""
		action_id = None

		if "action_id" in params:
			action_id = params["action_id"]
			if action_id is None:
				del params["action_id"]
		else:
			action_id = self.new_action_id()
			params["action_id"] = action_id

		action = Action(name, **params)

		if transient:
			assert self.session_id is not None
			action._transient_for_session_id = self.session_id

		return action

	def send_action(self, name, transient=False, **params):
		"""Create and send an action asynchronously.  See new_action for
		details.  The action_id is returned (if any).
		"""
		action = self.new_action(name, transient, **params)
		self.action_queue.put(action)
		return action.action_id

	def close(self):
		if self.__started and not self.__closed:
			self.__closed = True
			self.action_queue.put(self.CLOSE_SESSION)

	def _handle_send(self, action):
		pass

	def _handle_receive(self, event):
		caller_handles = True

		if not self._init.is_set():
			if event.name == "session_created":
				self.session_id = event._params["session_id"]
				self.session_host = event._params["session_host"]
				self._init.set()
			elif event.name == "error":
				if event.error_type == "session_not_found" and self.session_id is not None:
					self.__reset_session()
					caller_handles = False
				else:
					self.__terminate()

				self._init.set()
			else:
				log.warning("dropping unexpected event received before session_created: %r", event)
				caller_handles = False
		elif event.name == "error":
			if event.error_type == "session_not_found":
				self.__reset_session()
				caller_handles = False

		try:
			event_id = event._params.pop("event_id")
			if event_id is not None:
				self._event_id = event_id
		except KeyError:
			pass

		self._pending.ack(event)

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

				self._event_id = None
				last_event_id = None

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
					next_action, timeout = self._pending.get()
					if next_action is None:
						try:
							next_action = self.action_queue.get(timeout=timeout)
						except queue.Empty:
							continue

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
					log.debug("dropping transient %s", next_action)
					self._pending.drop(next_action)
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

				self._pending.sent(next_action)
				next_action = None

				if next_event_id is not None:
					last_event_id = next_event_id

	def _connect(self, action):
		url = self.url_format.format(self.session_host)

		while True:
			conn = self._connection_type(url, self)

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

class CallbackSessionBase(SessionBase):
	__doc__ = """Either the received(event) and closed() methods should be
	implemented in a subclass, or the received(session, event) and
	closed(session) callables should be passed to the constructor; they will be
	invoked when events are received.
	""" + SessionBase.__doc__ + """

	.. method:: create(**params)

	   Connect to the server and send the "create_session" action with given
	   parameters.  The received(event) method or the received(session, event)
	   callable will be invoked with a "session_created" event whenever a new
	   server session is established.

	.. method:: close()

	   Close the session (if created).  The closed() method or the
	   closed(session) callable will be invoked when done.

	"""

	def __init__(self, received=None, closed=None):
		super(CallbackSessionBase, self).__init__()
		self._received_callback = received or self.__class__.received
		self._closed_callback = closed or self.__class__.closed

	def received(self, event):
		pass

	def closed(self):
		pass

class QueueSessionBase(SessionBase):
	__doc__ = """Events are delivered via the receive_event() method, the
	event_queue or iteration.
	""" + SessionBase.__doc__ + """

	.. attribute:: event_queue

	   Queue for receiving Event objects; terminated by None.

	.. method:: create(**params)

	   Connect to the server and send the "create_session" action with given
	   parameters.  A "session_created" event will be delivered via the
	   event_queue whenever a new server session is established.

	.. method:: close()

	   Close the session (if created).  None will be delivered via event_queue
	   when done.

	"""
	def __init__(self):
		super(QueueSessionBase, self).__init__()
		self.event_queue = self.queue_type()
		self.__closed = False

	def __iter__(self):
		while True:
			event = self.receive_event()
			if event is None:
				break

			yield event

	def receive_event(self):
		"""Blocks until a new event is available.  Returns None when the
		session has been closed.
		"""
		if self.__closed:
			return None

		event = self.event_queue.get()
		if event is None:
			self.__closed = True

		return event
