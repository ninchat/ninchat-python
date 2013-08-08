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
	event.  The context manager protocol is supported: the session is closed in
	a blocking manner after the with-suite.

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
		"""Connect to the server and send the create_session action with given
		parameters.  The session_created (or error) event will be delivered via
		an implementation-specific mechanism.
		"""
		self.create_params = params
		self.__started = True
		self._sender.start()

	def new_action_id(self):
		"""Generate an action_id for an Action."""
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
		action = Action(name, **params)

		if transient:
			assert self.session_id is not None
			action._transient_for_session_id = self.session_id

		return action

	def send_action(self, name, transient=False, **params):
		"""Create and send an action asynchronously.  See new_action for
		details.  The action_id is returned (if any).
		"""
		action_id = None

		if "action_id" in params:
			action_id = params["action_id"]
			if action_id is None:
				del params["action_id"]
		else:
			action_id = self.new_action_id()
			params["action_id"] = action_id

		self.action_queue.put(self.new_action(name, transient, **params))

		return action_id

	def close(self):
		if self.__started and not self.__closed:
			self.__closed = True
			self.action_queue.put(self.CLOSE_SESSION)

class CallbackSessionBase(SessionBase):
	__doc__ = """Either the received(event) and closed() methods should be
	implemented in a subclass, or the received(session, event) and
	closed(session) callables should be passed to the constructor; they will be
	invoked when events are received.
	""" + SessionBase.__doc__ + """

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
