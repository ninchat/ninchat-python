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

import threading

try:
	# Python 2
	import Queue as queue
except ImportError:
	# Python 3
	import queue

import ws4py.client.threadedclient

from ninchat.client import log
from ninchat.client.event import Event
from ninchat.client.session import SynchronousSessionBase
from ninchat.client.session.websocket import ConnectionBase, TransportSessionBase

class Executor(threading.Thread):

	def __init__(self, target):
		super(Executor, self).__init__(target=target)

class Critical(object):

	def __init__(self, value):
		self.value = value
		self._lock = threading.Lock()

	def __enter__(self):
		self._lock.acquire()
		return self

	def __exit__(self, *exc):
		self._lock.release()

class Connection(ConnectionBase, ws4py.client.threadedclient.WebSocketClient):

	def __init__(self, hostname, session):
		super(Connection, self).__init__(hostname, session)
		self.event = None

	def received_message(self, message):
		event = self.event
		if event:
			event.payload.append(message.data)
			if len(event.payload) >= event._length:
				self.event = None
				self.session._received(event)
		elif message.data:
			event = Event(message.data)
			if event._length > 0:
				self.event = event
			else:
				self.session._received(event)

	def closed(self, code, reason):
		if self.event:
			log.warning("websocket connection closed in mid-event")

		self.session._disconnected()

class Session(TransportSessionBase):
	"""Asynchronous Ninchat client.  The received(event) and closed() methods
	should be overridden in a subclass.  They will be invoked in a dedicated
	thread.  During the session, actions may be sent by calling corresponding
	instance methods with keyword parameters; e.g.
	session.describe_user(user_id="0h6si071").
	"""
	connection_type = Connection
	critical_type = Critical
	executor_type = Executor
	flag_type = threading.Event
	queue_type = queue.Queue

	def _received(self, event):
		self._handle_receive(event)
		self.received(event)

	def _disconnected(self):
		if self._handle_disconnect():
			self.closed()

	def received(self, event):
		log.debug("Session.received method not implemented")

	def closed(self):
		log.debug("Session.closed method not implemented")

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
