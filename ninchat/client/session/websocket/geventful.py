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

try:
	# Python 2
	xrange
except NameError:
	# Python 3
	xrange = range

import gevent.queue

import ws4py.client.geventclient

from ninchat.client import log
from ninchat.client.event import Event
from ninchat.client.session import SynchronousSessionBase
from ninchat.client.session.websocket import ConnectionBase, TransportSessionBase

class Critical(object):

	def __init__(self, value):
		self.value = value

	def __enter__(self):
		return self

	def __exit__(self, *exc):
		pass

class Connection(ConnectionBase, ws4py.client.geventclient.WebSocketClient):

	def opened(self):
		gevent.spawn(self._receive_loop)

	def _receive_loop(self):
		while True:
			message = self.receive()
			if message is None:
				self.session._receive_queue.put(None)
				return

			if not message.data:
				continue

			event = Event(message.data)

			for _ in xrange(event._length):
				message = self.receive()
				if message is None:
					log.warning("websocket connection closed in mid-event")
					self.session._receive_queue.put(None)
					return

				event.payload.append(message.data)

			self.session._receive_queue.put(event)

class Session(TransportSessionBase, SynchronousSessionBase):
	"""A Ninchat client for use with the gevent module.  During the session,
	actions may be sent by calling corresponding instance methods with keyword
	parameters; e.g.  session.describe_user(user_id="0h6si071").
	"""
	connection_type = Connection
	critical_type = Critical
	executor_type = gevent.Greenlet
	flag_type = gevent.event.Event
	queue_type = gevent.queue.Queue

	def __init__(self):
		super(Session, self).__init__()
		self._receive_queue = self.queue_type()

	def receive(self):
		while True:
			event = self._receive_queue.get()
			if event is not None:
				self._handle_receive(event)
				return event

			if self._handle_disconnect():
				return None
