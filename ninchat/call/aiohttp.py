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

__all__ = ["call", "check_call"]

import asyncio
from http import HTTPStatus
from typing import Any, Dict, Optional

import aiohttp

from .. import call as lib


async def call(session: aiohttp.ClientSession,
               params: Dict[str, Any],
               *,
               identity: Optional[Dict[str, str]] = None,
               check: bool = False
               ) -> Dict[str, Any]:
    """An asyncio coroutine which makes a HTTP request to the
       Ninchat Call API using the third-party aiohttp package.

       If check is set, raises a ninchat.call.APIError on "error" reply
       event.
    """
    data = lib.request_content(params, identity=identity)
    async with session.post(lib.url, data=data, headers=lib.request_headers) as r:
        if r.status != HTTPStatus.OK:
            r.raise_for_status()
        e = await r.json()

    if check:
        lib.check_event(e)

    return e


@asyncio.coroutine
def check_call(session: aiohttp.ClientSession,
               params: Dict[str, Any],
               *,
               identity: Optional[Dict[str, str]] = None
               ) -> Dict[str, Any]:
    """Like call with check set."""
    return call(session, params, identity=identity, check=True)
