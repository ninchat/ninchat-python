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

__all__ = ["Error", "Session"]

import asyncio
from typing import Any, ByteString, Callable, Dict, List, Optional, Sequence, Tuple

from . import Error
from . import Session as BaseSession


class Session(BaseSession):

    def __init__(self,
                 loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        super().__init__()
        self.loop = loop or asyncio.get_event_loop()
        self.opened = self.loop.create_future()
        self.closed = self.loop.create_future()

    def open(self,
             on_reply: Optional[Callable[[Dict[str, Any]], None]] = None,
             ) -> asyncio.Future:
        if on_reply:
            def callback(params):
                self.opened.set_result(params)
                on_reply(params)
        else:
            callback = self.opened.set_result

        super().open(callback)
        return self.opened

    def close(self) -> asyncio.Future:
        super().close()
        return self.closed

    async def call(self,
                   params: Dict[str, Any],
                   payload: Optional[Sequence[ByteString]] = None,
                   ) -> Tuple[Dict[str, Any], List[bytes]]:
        f = self.loop.create_future()

        def on_reply(params, payload, last_reply):
            if last_reply:
                f.set_result((params, payload))

        self.send(params, payload, on_reply)
        return await f

    def _handle_close(self):
        try:
            super()._handle_close()
        finally:
            self.closed.set_result(None)

    def _call(self, call, *args):
        self.loop.call_soon_threadsafe(call, *args)
