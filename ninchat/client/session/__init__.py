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

from ninchat.client.action import Action, SessionAction

class SessionBase(object):
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

	def _connect(self, action):
		self.conn = self.connection_type(self, action)
		self.conn.connect()

	def _process(self, event):
		if event.type == "session_created":
			self.session_id = event._params.pop("session_id")
			self.session_host = event._params.pop("session_host")

		try:
			self.event_id = event._params.pop("event_id")
		except KeyError:
			pass

		return event

	def create(self, **params):
		"""Connect to the server and send the create_session action with given
		parameters.  The session_created (or error) event will be delivered via
		an implementation-specific mechanism.
		"""
		assert not self.conn
		self._connect(Action("create_session", **params))

	def close(self):
		"""Close the session and server connection (if any).  Notification
		about the session closure is delivered via an implementation-specific
		mechanism.
		"""
		if not self.conn or self.closing:
			return

		session_id = self.session_id
		self.session_id = None
		self.closing = True

		if session_id is not None:
			self.conn.send_action(SessionAction("close_session"))

	def __getattr__(self, name):
		def call(**params):
			assert self.conn

			action_id = None

			if "action_id" in params:
				action_id = params["action_id"]
				if action_id is None:
					del params["action_id"]
			else:
				self.action_id += 1
				action_id = self.action_id
				params["action_id"] = action_id

			self.conn.send_action(Action(name, self.event_id, **params))
			self.event_id = None

			return action_id

		return call

class SynchronousSessionBase(SessionBase):

	def __iter__(self):
		while True:
			event = self.receive()
			if event is None:
				break
			yield event
