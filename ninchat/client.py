# Copyright (c) 2012, Somia Reality Oy
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

"""Tools for implementing Ninchat API clients.

Module contents:
log -- a logging.Logger which may be configured by the application
ThreadedSession
QueuedSession
Event
ParameterError
"""

import json
import logging

try:
	# Python 3
	import queue
except ImportError:
	# Python 2
	import Queue as queue

import ws4py.client.threadedclient

from . import api

log = logging.getLogger("ninchat.client")

class ParameterError(Exception):
	"""API action is missing a required parameter or the parameter value is
	invalid.  The corresponding ninchat.api.Parameter instance may be read from
	the param attribute.
	"""
	def __init__(self, param, message):
		super(ParameterError, self).__init__(message)
		self.param = param

class Action(object):

	def __init__(self, action, event_id=None, payload=None, **params):
		self._params = params
		self.payload = payload or []

		specs = api.actions[action].params

		for name, spec in specs.items():
			value = self._params.get(name)
			if value is None:
				if spec.required:
					raise ParameterError(
							spec,
							"%r is missing from %r action" % (name, action))
			else:
				if not spec.validate(value):
					raise ParameterError(
							"%r value is invalid in %r action: %r" %
							(name, action, value))

		for name in self._params:
			if name not in specs:
				raise ParameterError(
						"unknown %r in %r action" % (name, action))

		self._params["action"] = action

		if event_id is not None:
			self._params["event_id"] = event_id

		if self.payload:
			self._params["frames"] = len(self.payload)

	def __str__(self):
		return self._params["action"]

	def __repr__(self):
		return "<Action %r %s%s>" % (
			self._params["action"],
			" ".join(
					"%s %r" % (k, v) for k, v in sorted(self._params.items())
					if k not in ("action", "frames")),
			(" payload " + " ".join(
					"%r" % p for p in self.payload)) if self.payload else "")

	@property
	def frames(self):
		return [json.dumps(self._params, separators=(",", ":"))] + self.payload

class SessionAction(Action):

	def __init__(self, action, session_id=None, event_id=None):
		self._params = { "action": action }
		self.payload = []

		if session_id is not None:
			self._params["session_id"] = session_id

		if event_id is not None:
			self._params["event_id"] = event_id

class Event(object):
	"""Holds an API event received from the server.  Event parameters may be
	accessed as instance attributes (the type name of the event can be read
	from the type attribute).  Optional parameters default to None.  The
	payload attribute contains a list of bytes objects.
	"""
	def __init__(self, frame):
		self._params = json.loads(frame.decode("utf-8"))
		self._length = self._params.pop("frames", 0)
		self.payload = []

	@property
	def type(self):
		return self._params["event"]

	def __getattr__(self, name):
		spec = api.events[self.type].params[name]
		value = self._params.get(name)
		if value is None and spec.required:
			log.warning("event %r parameter %r is missing", event, name)
		return value

	def __str__(self):
		return self._params["event"]

	def __repr__(self):
		return "<Event %r %s%s>" % (
			self._params.get("event"),
			" ".join(
					"%s %r" % (k, v) for k, v in sorted(self._params.items())
					if k != "event"),
			(" payload " + " ".join(
					"%r" % p for p in self.payload)) if self.payload else "")

class ThreadedSession(object):
	"""Asynchronous Ninchat client.  The received(event) and closed() methods
	should be overridden in a subclass.  They will be invoked in a dedicated
	thread.  During the session, actions may be sent by calling corresponding
	instance methods with keyword parameters; e.g.
	session.describe_user(user_id="0h6si071").
	"""
	class Connection(ws4py.client.threadedclient.WebSocketClient):

		url_format = "wss://{}/socket"
		protocol = "ninchat.com/1"

		def __init__(self, session, action):
			super(ThreadedSession.Connection, self).__init__(
					self.url_format.format(session.session_host),
					[self.protocol])

			self.session = session
			self.action = action
			self.event = None

		def send_action(self, action):
			for frame in action.frames:
				self.send(frame)

		def opened(self):
			self.send_action(self.action)
			del self.action

		def received_message(self, message):
			frame = message.data
			event = self.event
			if event:
				event.payload.append(frame)
				if len(event.payload) >= event._length:
					self.event = None
					self.session._received(event)
			elif frame:
				event = Event(frame)
				if event._length > 0:
					self.event = event
				else:
					self.session._received(event)

		def closed(self, code, reason):
			self.session._disconnected()

	session_host = "api.ninchat.com"
	session_id = None
	action_id = 0
	event_id = None

	def __init__(self):
		"""New, unestablished user session.  The create() method must be called
		before doind anything productive.
		"""
		self.closing = False
		self.conn = None

	def __enter__(self):
		return self

	def __exit__(self, *exc):
		self.close()

	def create(self, **params):
		"""Connect to the server and send the create_session action with given
		parameters.  The session_created (or error) event will be delivered via
		the received(event) method.
		"""
		assert not self.conn
		self.conn = self.Connection(self, Action("create_session", **params))
		self.conn.connect()

	def _received(self, event):
		if event.type == "session_created":
			self.session_id = event._params.pop("session_id")
			self.session_host = event._params.pop("session_host")

		try:
			self.event_id = event._params.pop("event_id")
		except KeyError:
			pass

		self.received(event)

		if self.event_id is not None:
			self.conn.send_action(
					SessionAction("resume_session", event_id=self.event_id))
			self.event_id = None

	def __getattr__(self, name):
		def call(**params):
			assert self.conn

			self.action_id += 1
			action_id = self.action_id

			self.conn.send_action(Action(name, self.event_id, action_id=action_id, **params))
			self.event_id = None

			return action_id

		return call

	def close(self):
		"""Close the session and server connection (if any).  The closed()
		method is invoked when finished.
		"""
		if not self.conn or self.closing:
			return

		session_id = self.session_id
		self.session_id = None
		self.closing = True

		if session_id is not None:
			self.conn.send_action(SessionAction("close_session"))

	def _disconnected(self):
		if self.closing:
			self.conn = None
			self.closed()
			return

		if self.session_id is None:
			self.conn = self.Connection(
					self, SessionAction("resume_session", self.session_id))
			self.conn.connect()

	def received(self, event):
		log.debug("ThreadedSession.received method not implemented")

	def closed(self):
		log.debug("ThreadedSession.closed method not implemented")

class QueuedSession(ThreadedSession):
	"""Synchronous Ninchat client.  Events are delivered via the blocking
	receive() call or iteration.  Between events, actions may be sent by
	calling corresponding instance methods with keyword parameters; e.g.
	session.describe_user(user_id="0h6si071").
	"""
	def __init__(self):
		super(QueuedSession, self).__init__()
		self.queue = queue.Queue()

	def create(self, **params):
		"""Connect to the server and send the create_session action with given
		parameters.  Wait for and return the session_created (or error) event.
		"""
		super(QueuedSession, self).create(**params)
		return self.receive()

	def receive(self):
		"""Get the next event, or None if session closed.
		"""
		while True:
			try:
				# using a timeout fixes Python 2 uninterruptability problem
				return self.queue.get(timeout=1 << 31)
			except queue.Empty:
				pass

	def __iter__(self):
		while True:
			event = self.receive()
			if event is None:
				break
			yield event

	def close(self):
		"""Close the session and server connection (if any).  None is delivered
		via receive() or the iterator when finished.
		"""
		super(QueuedSession, self).close()

	def received(self, event):
		self.queue.put(event)

	def closed(self):
		self.queue.put(None)
