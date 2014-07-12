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

from __future__ import absolute_import

from .. import api
from .action import Action

class SyncCreation(object):

	def __init__(self, flag_type):
		self.flag = flag_type()

	@property
	def result(self):
		self.flag.wait()
		return self.event

	def done(self, event):
		self.event = event
		self.flag.set()

class AsyncCreation(object):

	def __init__(self, session, callback):
		self.session = session
		self.callback = callback

	def done(self, event):
		self.callback(self.session, event)

class Call(object):

	def __init__(self, session, action):
		self.session = session
		self.action = action
		self.events = []

	@property
	def more_events(self):
		return not self.events or self.action.multiple_events

class SyncCall(Call):

	def __init__(self, session, action, flag_type):
		super(SyncCall, self).__init__(session, action)
		self.flag = flag_type()

	@property
	def result(self):
		self.flag.wait()
		if self.action.multiple_events:
			return self.events
		else:
			return self.events[0]

	def deliver(self):
		self.flag.set()

	def close(self):
		self.events = None
		self.deliver()

class AsyncCall(Call):

	def __init__(self, session, action, callback):
		super(AsyncCall, self).__init__(session, action)
		self.callback = callback

	def deliver(self):
		if self.action.multiple_events:
			self.callback(self.session, self.action, self.events)
		else:
			self.callback(self.session, self.action, self.events[0])

	def close(self):
		self.callback(self.session, self.action, None)

class Registry(object):

	def __init__(self):
		self.calls = {}
		self.transients = set()

	def register(self, action_id, call, transient):
		self.calls[action_id] = call
		if transient:
			self.transients.add(action_id)

	def __delitem__(self, action_id):
		del self.calls[action_id]
		try:
			self.transients.remove(action_id)
		except KeyError:
			pass

	def get(self, action_id):
		return self.calls.get(action_id)

	def pop_transients(self):
		transients = self.transients
		self.transients = set()
		return [self.calls.pop(action_id) for action_id in transients]

	def rip_all(self):
		calls = self.calls
		self.calls = None
		self.transients = None
		return calls

class AdapterBase(object):
	"""
	.. attribute:: action_queue

	   See session.

	.. method:: new_action(name, transient=False, **params)

	   See session.

	.. method:: send_action(name, transient=False, **params)

	   See session.

	.. method:: close()

	   See session.

	"""
	def __init__(self, session):
		super(AdapterBase, self).__init__()
		self._session = session
		self._creation = None
		self._registry = session._critical_type(Registry())

	def __enter__(self):
		return self

	def __exit__(self, *exc):
		self._session.__exit__(*exc)

	def __getattr__(self, name):
		if name not in api.actions:
			return getattr(self._session, name)

		def call(*call_args, **params):
			if params.get("action_id", True) is None:
				assert not call_args
				return self._session.send_action(name, **params)
			else:
				return self.call_action(name, *call_args, **params)

		return call

	def _call(self, name, transient, action_params, *call_args):
		action = self._session.new_action(name, transient, **action_params)
		assert action.action_id is not None

		call = self._call_type(self._session, action, *call_args)

		with self._registry as critical:
			critical.value.register(action.action_id, call, transient)

		self._session.action_queue.put(action)

		return call

	def _handle_receive(self, event):
		if self._creation is not None:
			c = self._creation
			self._creation = None
			c.done(event)
			return True

		if event.name == "session_created":
			with self._registry as critical:
				transient_calls = critical.value.pop_transients()

			for call in transient_calls:
				call.close()

			return False

		action_id = event._params.get("action_id")
		if action_id is None:
			return False

		with self._registry as critical:
			call = critical.value.get(action_id)
			if not call:
				return False

			call.events.append(event)
			if call.more_events:
				return True

			del critical.value[action_id]

		call.deliver()
		return True

	def _handle_close(self):
		with self._registry as critical:
			all_calls = critical.value.rip_all()

		for call in all_calls.values():
			call.close()

		if self._creation is not None:
			c = self._creation
			self._creation = None
			c.done(None)

class SyncAdapterBase(AdapterBase):
	__doc__ = """The instance methods corresponding to API actions are
	implemented using call_action if applicable; the call is synchronous if the
	action uses an action_id.
	""" + AdapterBase.__doc__

	_call_type = SyncCall

	def create(self, **params):
		"""Like the session object's create method, but wait for and return the
		response event.  None is returned if the session is closed before it
		could be established.

		Additional "session_created" events are delivered with the other
		unsolicited events if the server session needs to be reset.
		"""
		self._creation = c = SyncCreation(self._session._flag_type)
		self._session.create(**params)
		return c.result

	def call_action(self, name, transient=False, **params):
		"""Like the session object's send_action method, but wait for a
		response.  The action_id parameter is generated implicitly unless
		specified by the caller.  Depending on action type, either a single
		event or a list of events is returned.  None is returned if the session
		is closed before the response is received.
		"""
		return self._call(name, transient, params, self._session._flag_type).result

class AsyncAdapterBase(AdapterBase):
	__doc__ = """The instance methods corresponding to API actions are
	implemented using call_action if applicable; the first positional parameter
	must be a callback if the action uses an action_id.
	""" + AdapterBase.__doc__

	_call_type = AsyncCall

	def create(self, callback, **params):
		"""Like the session object's create method, and call callback(session,
		event) when a response is received.  The event parameter will be None
		if the session is closed before it could be established.

		Somewhat surprisingly, additional "session_created" events are
		delivered with the other unsolicited events if the server session needs
		to be reset.
		"""
		self._creation = AsyncCreation(self._session, callback)
		self._session.create(**params)

	def call_action(self, name, callback, transient=False, **params):
		"""Like the session object's send_action method, and call
		callback(session, action, event_or_events) when a response is received.
		The action_id parameter is generated implicitly unless specified by the
		caller.  Depending on action type, either a single event or a list of
		events are passed to the callback.  The event_or_events parameter will
		be None if the session is closed before the response is received.
		"""
		self._call(name, transient, params, callback)

class CallbackBase(object):

	def __init__(self, session):
		super(CallbackBase, self).__init__(session)

		self._received_callback = session._received_callback
		self._closed_callback = session._closed_callback

		session._received_callback = self._received
		session._closed_callback = self._closed

	def _received(self, session, event):
		if not self._handle_receive(event):
			self._received_callback(session, event)

	def _closed(self, session):
		self._handle_close()
		self._closed_callback(session)

class QueueBase(object):

	def __iter__(self):
		while True:
			event = self.receive_event()
			if event is None:
				break

			yield event

	def receive_event(self):
		while True:
			event = self._session.receive_event()
			if event is None:
				self._handle_close()
				return None

			if not self._handle_receive(event):
				return event

class SyncCallbackAdapter(CallbackBase, SyncAdapterBase):
	__doc__ = """CallbackSession adapter providing synchronous action calls.
	(Surprisingly, unsolicited events are delivered via the session instance's
	callbacks.)
	""" + SyncAdapterBase.__doc__

class SyncQueueAdapter(QueueBase, SyncAdapterBase):
	__doc__ = """QueueSession adapter providing synchronous action calls.
	""" + SyncAdapterBase.__doc__ + """

	.. method:: receive_event()

	   Blocks until a new unsolicited event (one that is not a response to a
	   synchronous call) is available.  Returns None when the session has been
	   closed.

	   Note: this method drives the machinery which also delivers the
	   synchronous calls' responses, so the user must arrange for it to be
	   called often enough.

	"""

class AsyncCallbackAdapter(CallbackBase, AsyncAdapterBase):
	__doc__ = """CallbackSession adapter providing individual callbacks for
	action calls.
	""" + AsyncAdapterBase.__doc__

class AsyncQueueAdapter(QueueBase, AsyncAdapterBase):
	__doc__ = """QueueSession adapter providing individual callbacks for action
	calls.  (Surprisingly, unsolicited events are delivered via the
	receive_event method.)
	""" + AsyncAdapterBase.__doc__ + """

	.. method:: receive_event()

	   Blocks until a new unsolicited event (one that has not been subscribed
	   to by a call) is available.  Returns None when the session has been
	   closed.

	   Note: this method drives the machinery which also invokes the callbacks,
	   so the user must arrange for it to be called often enough.

	"""
