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

from __future__ import absolute_import

import sys
import threading

import ws4py.client.threadedclient

from ... import log
from ...event import Event
from .. import CallbackSessionBase, QueueSessionBase
from . import CallbackConnectionBase, ConnectionBase, QueueConnectionBase, TransportSessionBase

if sys.version_info[0] == 2:
	import Queue as queue

	class Queue(queue.Queue):

		def __init__(self, *args, **kwargs):
			self.__impl = queue.Queue(*args, **kwargs)

		def __getattr__(self, name):
			return getattr(self.__impl, name)

		def get(self, timeout=None):
			# using a timeout fixes Python 2 uninterruptability problem
			if timeout is None:
				timeout = 0x7fffffff

			return self.__impl.get(timeout=timeout)
else:
	from queue import Queue

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

class AbstractConnection(ConnectionBase, ws4py.client.threadedclient.WebSocketClient):

	def __init__(self, hostname, session):
		super(AbstractConnection, self).__init__(hostname, session)
		self._event = None

	def received_message(self, message):
		event = self._event
		if event:
			event.payload.append(message.data)
			if len(event.payload) >= event._length:
				self._event = None
				self._received(event)
		elif message.data:
			event = Event(message.data)
			if event._length > 0:
				self._event = event
			else:
				self._received(event)

	def closed(self, code, reason):
		if self._event:
			log.warning("websocket connection closed in mid-event")

		self._closed()

class AbstractSession(TransportSessionBase):
	queue_type = Queue
	_critical_type = Critical
	_executor_type = Executor
	_flag_type = threading.Event

class CallbackConnection(CallbackConnectionBase, AbstractConnection):
	pass

class CallbackSession(CallbackSessionBase, AbstractSession):
	__doc__ = CallbackSessionBase.__doc__
	_connection_type = CallbackConnection

class QueueConnection(QueueConnectionBase, AbstractConnection):
	pass

class QueueSession(QueueSessionBase, AbstractSession):
	__doc__ = QueueSessionBase.__doc__
	_connection_type = QueueConnection
