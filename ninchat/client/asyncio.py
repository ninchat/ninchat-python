# Copyright (c) 2017, Somia Reality Oy
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

""  # Enables documentation generation.

__all__ = ["Session"]

import asyncio

try:
    from typing import Any, ByteString, Callable, Dict, Optional, Sequence
    (Any, ByteString, Callable, Dict, Optional, Sequence)  # silence typing warnings
except ImportError:
    pass

try:
    # Python 3.5+
    asyncio.AbstractEventLoop.create_future

    def _create_future(*, loop):
        return loop.create_future()
except AttributeError:
    # Python 3.4
    _create_future = asyncio.Future

from . import Session as BaseSession


class Session(BaseSession):
    """A version of ninchat.client.Session which executes callbacks
    in the asyncio event loop.

    .. attribute:: opened

       A future which provides the session_created event's parameters once the
       session has been created (for the first time).

    .. attribute:: closed

       A future which will be marked as done once the session closing is
       complete.
"""

    def __init__(self, *, loop=None):
        # type: (Optional[asyncio.AbstractEventLoop]) -> None

        super().__init__()

        self.loop = loop or asyncio.get_event_loop()
        self.opened = _create_future(loop=self.loop)
        self.closed = _create_future(loop=self.loop)
        self._closing = False

    def __aenter__(self):
        if self.state == "uninitialized":
            self.open()
        return self.opened

    def __aexit__(self, *exc):
        if not self._closing:
            self.close()
        return self.closed

    def open(self, on_reply=None):
        # type: (Optional[Callable[[Dict[str, Any]], None]]) -> asyncio.Future
        """Like ninchat.client.Session.open(), but returns a
        future.  The on_reply callback is supported for interface
        compatibility."""

        def callback(params):
            if params is None:
                self.opened.cancel()
            else:
                self.opened.set_result(params)

            if on_reply:
                on_reply(params)

        super().open(callback)
        return self.opened

    def close(self):
        # type: () -> asyncio.Future
        """Like ninchat.client.Session.close(), but returns a
        future."""

        super().close()
        self._closing = True
        return self.closed

    def call(self, params, payload=None, on_reply=None):
        # type: (Dict[str,Any], Optional[Sequence[ByteString]], Optional[Callable[[Dict[str,Any], List[bytes], bool], None]]) -> asyncio.Future
        """An awaitable version of ninchat.client.Session.send().
        Returns the final reply event's params and payload."""

        f = _create_future(loop=self.loop)

        def callback(params, payload, last_reply):
            if params is None:
                f.cancel()
            else:
                try:
                    if on_reply is not None:
                        on_reply(params, payload, last_reply)
                finally:
                    if last_reply:
                        f.set_result((params, payload))

        self.send(params, payload, callback)
        return f

    def _handle_close(self):
        try:
            super()._handle_close()
        finally:
            self.closed.set_result(None)

    def _call(self, call, *args):
        self.loop.call_soon_threadsafe(call, *args)
