# Copyright (c) 2013-2017, Somia Reality Oy
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

"""Session implementations using the third-party gevent module.

.. autoclass:: CallbackSession
   :members: create, close, new_action, send_action

.. autoclass:: QueueSession
   :members: create, close, new_action, send_action, receive_event

"""

from __future__ import absolute_import

__all__ = ["CallbackSession", "QueueSession"]

try:
    # Python 2
    xrange
except NameError:
    # Python 3
    xrange = range

import gevent.event
import gevent.queue

import ws4py.client.geventclient

from .. import log
from ..event import Event

from . import (
    CallbackConnectionBase,
    ConnectionBase,
    QueueConnectionBase,
    SessionBase,
    CallbackSessionBase,
    QueueSessionBase,
)


class Critical(object):

    def __init__(self, value=None):
        if value is not None:
            self.value = value

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        pass


class AbstractConnection(ConnectionBase, ws4py.client.geventclient.WebSocketClient):

    def opened(self):
        gevent.spawn(self._receive_loop)

    def _receive_loop(self):
        while True:
            message = self.receive()
            if message is None:
                self._closed()
                return

            if not message.data:
                continue

            event = Event(message.data)

            for _ in xrange(event._length):
                message = self.receive()
                if message is None:
                    log.warning("websocket connection closed in mid-event")
                    self._closed()
                    return

                event.payload.append(message.data)

            self._received(event)


class AbstractSession(SessionBase):
    queue_type = gevent.queue.Queue
    _critical_type = Critical
    _executor_type = gevent.Greenlet
    _flag_type = gevent.event.Event


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
