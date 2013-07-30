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

from ninchat.client.action import Action

class SessionBase(object):
	CLOSE_SESSION = object()
	SESSION_CLOSED = object()

	session_host = "api.ninchat.com"

	def __init__(self):
		"""New, unestablished user session.  The create() method must be called
		before doind anything productive.
		"""
		self.session_id = None
		self.action_id = self.critical_type(0)
		self.event_id = None
		self.__started = False
		self.__closed = False
		self._init = self.flag_type()
		self._send_queue = self.queue_type(1)
		self._sender = self.executor_type(self._send_loop)

	def __enter__(self):
		return self

	def __exit__(self, *exc):
		self.close()

	def __getattr__(self, action):
		def call(**params):
			return self.send_action(action, **params)

		return call

	def _handle_send(self, action):
		pass

	def _handle_receive(self, event):
		if event.type == "session_created":
			self.session_id = event._params.pop("session_id")
			self.session_host = event._params.pop("session_host")

		self._init.set()

		try:
			event_id = event._params.pop("event_id")
			if event_id is not None:
				self.event_id = event_id
		except KeyError:
			pass

	def _handle_disconnect(self):
		self._init.set()

		if self._closing:
			self._send_queue.put(self.SESSION_CLOSED)
			return True
		else:
			self._reconnect = True
			self._send_queue.put(None)
			return False

	def create(self, **params):
		"""Connect to the server and send the create_session action with given
		parameters.  The session_created (or error) event will be delivered via
		an implementation-specific mechanism.
		"""
		self.create_params = params
		self.__started = True
		self._sender.start()

	def send_action(self, action, **params):
		"""Send the named action asynchronously.  The action_id parameter is
		generated implicitly (if applicable), unless it is disabled by
		specifying it as None.  The generated action_id is returned.
		"""
		assert self.session_id is not None

		action_id = None

		if "action_id" in params:
			assert params["action_id"] is None
			del params["action_id"]
		else:
			with self.action_id as critical:
				critical.value += 1
				action_id = critical.value

			params["action_id"] = action_id

		self._send_queue.put(Action(action, **params))

		return action_id

	def close(self):
		"""Close the session and server connection (if any).  Notification
		about the session closure is delivered via an implementation-specific
		mechanism.
		"""
		if self.__started and not self.__closed:
			self.__closed = True
			self._send_queue.put(self.CLOSE_SESSION)
			self._sender.join()

class SynchronousSessionBase(SessionBase):

	def __iter__(self):
		while True:
			event = self.receive()
			if event is None:
				break
			yield event
