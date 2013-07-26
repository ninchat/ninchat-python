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

try:
	# Python 2
	import Queue as queue
except ImportError:
	# Python 3
	import queue

from ninchat.client import log
from ninchat.client.action import Action, SessionAction
from ninchat.client.session import SessionBase, SynchronousSessionBase
from ninchat.client.websocket.threaded import Connection

class Session(SessionBase):
	"""Asynchronous Ninchat client.  The received(event) and closed() methods
	should be overridden in a subclass.  They will be invoked in a dedicated
	thread.  During the session, actions may be sent by calling corresponding
	instance methods with keyword parameters; e.g.
	session.describe_user(user_id="0h6si071").
	"""
	connection_type = Connection

	def _received(self, event):
		self.received(self._process(event))

		if self.event_id is not None:
			self.conn.send_action(SessionAction("resume_session", event_id=self.event_id))
			self.event_id = None

	def _disconnected(self):
		self.conn = None

		if self.closing or self.session_id is None:
			self.closed()
		else:
			self._connect(SessionAction("resume_session", self.session_id))

	def received(self, event):
		log.debug("ThreadedSession.received method not implemented")

	def closed(self):
		log.debug("ThreadedSession.closed method not implemented")

class QueuedSession(Session, SynchronousSessionBase):
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

	def received(self, event):
		self.queue.put(event)

	def closed(self):
		self.queue.put(None)
