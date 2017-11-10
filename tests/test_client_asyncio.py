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

import asyncio
import sys
import logging
from functools import partial
from glob import glob

sys.path.insert(0, "")
sys.path = glob("build/lib.*/") + sys.path

from ninchat.client.asyncio import Session

log = logging.getLogger("test_client_asyncio")


async def test():
    def on_session_event(params):
        pass

    def on_event(params, payload, last_reply):
        if params["event"] == "message_received":
            log.debug("received %s", payload[0].decode())

    s = Session()
    s.on_session_event = on_session_event
    s.on_event = on_event
    s.set_params({"user_attrs": {"name": "ninchat-python"}, "message_types": ["*"]})

    async with s as params:
        log.debug("opened params = %s", params)
        user_id = params["user_id"]

        params, _ = await s.call({"action": "describe_conn"})
        log.debug("called params = %s", params)

        await s.call({"action": "send_message", "message_type": "ninchat.com/text", "user_id": user_id}, [b'{"text": "Hello, me!"}'])

    log.info("ok")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(test())
