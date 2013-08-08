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

class AdapterBase(object):
	"""
	.. attribute:: event_queue

	   See session.

	.. method:: new_action_id()

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
		self._calls = session._critical_type({})

	def __enter__(self):
		return self

	def __exit__(self, *exc):
		self.close()

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

	def _call(self, name, action_params, *call_args):
		if "action_id" in action_params:
			action_id = action_params["action_id"]
			assert action_id is not None
		else:
			action_id = self._session.new_action_id()
			action_params["action_id"] = action_id

		action = self._session.new_action(name, **action_params)
		call = self._call_type(self._session, action, *call_args)

		with self._calls as critical:
			critical.value[action_id] = call

		self._session.action_queue.put(action)

		return call

	def _handle_receive(self, event):
		if self._creation is not None:
			c = self._creation
			self._creation = None
			c.done(event)
			return True

		action_id = event._params.get("action_id")
		if action_id is None:
			return False

		with self._calls as critical:
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
		with self._calls as critical:
			calls = critical.value
			critical.value = None

		for call in calls.itervalues():
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
		"""Call the session instances's create method, and wait for and return
		the response event.  None is returned if the session is closed before
		it could be established.
		"""
		self._creation = c = SyncCreation(self._session._flag_type)
		self._session.create(**params)
		return c.result

	def call_action(self, name, **params):
		"""Call the session instance's send_action method, and wait for a
		response.  The action_id parameter is generated implicitly unless
		specified by the caller.  Depending on action type, either a single
		event or a list of events is returned.  None is returned if the session
		is closed before the response is received.
		"""
		return self._call(name, params, self._session._flag_type).result

class AsyncAdapterBase(AdapterBase):
	__doc__ = """The instance methods corresponding to API actions are
	implemented using call_action if applicable; the first positional parameter
	must be a callback if the action uses an action_id.
	""" + AdapterBase.__doc__

	_call_type = AsyncCall

	def create(self, callback, **params):
		"""Call the session instances's create method, and call
		callback(session, event) when a response is received.  The event
		parameter will be None if the session is closed before it could be
		established.
		"""
		self._creation = AsyncCreation(self._session, callback)
		self._session.create(**params)

	def call_action(self, name, callback, **params):
		"""Call the session instance's send_action method, and call
		callback(session, action, event_or_events) when a response is received.
		The action_id parameter is generated implicitly unless specified by the
		caller.  Depending on action type, either a single event or a list of
		events are passed to the callback.  The event_or_events parameter will
		be None if the session is closed before the response is received.
		"""
		self._call(name, params, callback)

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
