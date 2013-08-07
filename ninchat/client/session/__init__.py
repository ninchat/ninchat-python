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

from ... import api
from ..action import Action

class SessionBase(object):
	"""Actions may be sent via the send_action() method, the action_queue or by
	calling corresponding instance methods with keyword parameters;
	e.g. session.describe_user(user_id="0h6si071").  The session must be
	established by calling create() and waiting for the "session_created"
	event.

	.. attribute:: action_queue

	   Queue for sending Action objects.

	"""
	CLOSE_SESSION = object()

	session_host = "api.ninchat.com"

	def __init__(self):
		self.action_queue = self.queue_type()
		self.session_id = None
		self._action_id = self._critical_type(0)
		self._event_id = None
		self._sender = self._executor_type(self._send_loop)
		self.__started = False
		self.__closed = False

	def __enter__(self):
		return self

	def __exit__(self, *exc):
		self.close()

	def __getattr__(self, action):
		if action not in api.actions:
			raise AttributeError(action)

		def call(**params):
			return self.send_action(action, **params)

		return call

	def create(self, **params):
		"""Connect to the server and send the create_session action with given
		parameters.  The session_created (or error) event will be delivered via
		an implementation-specific mechanism.
		"""
		self.create_params = params
		self.__started = True
		self._sender.start()

	def next_action_id(self):
		"""Generate an action_id for an Action."""
		with self._action_id as critical:
			critical.value += 1
			return critical.value

	def send_action(self, action, **params):
		"""Send the named action asynchronously.  The action_id parameter is
		generated implicitly (if applicable) unless specified by the caller.
		The action_id is returned.
		"""
		action_id = None

		if "action_id" in params:
			action_id = params["action_id"]
			if action_id is None:
				del params["action_id"]
		else:
			action_id = self.next_action_id()
			params["action_id"] = action_id

		self.action_queue.put(Action(action, **params))

		return action_id

	def close(self):
		"""Close the session and server connection (if any).  Notification
		about the session closure is delivered via an implementation-specific
		mechanism.
		"""
		if self.__started and not self.__closed:
			self.__closed = True
			self.action_queue.put(self.CLOSE_SESSION)
			self._sender.join()

class CallbackSessionBase(SessionBase):
	__doc__ = """Either the received(event) and closed() methods should be
	implemented in a subclass, or the received(session, event) and
	closed(session) callables should be passed to the constructor; they will be
	invoked when events are received.
	""" + SessionBase.__doc__

	def __init__(self, received=None, closed=None):
		super(CallbackSessionBase, self).__init__()
		self._received_callback = received or self.__class__.received
		self._closed_callback = closed or self.__class__.closed

class QueueSessionBase(SessionBase):
	__doc__ = """Events are delivered via the receive_event() method, the
	event_queue or iteration.
	""" + SessionBase.__doc__ + """

	.. attribute:: event_queue

	   Queue for receiving Event objects; terminated by None.

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
