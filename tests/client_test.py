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

from __future__ import absolute_import

import json
import logging

from ninchat.client import Session

try:
    # Python 3
    from queue import Queue
except ImportError:
    # Python 2
    from Queue import Queue

log = logging.getLogger(__name__)


def test_client(session_type=Session, queue_type=Queue):
    user_ids = queue_type()
    messages = queue_type()
    closed = queue_type()

    def on_session_event(params):
        log.debug("session event: %s", params)
        user_ids.put(params["user_id"])

    def on_event(params, payload, last_reply):
        log.debug("event: %s, payload: %s", params, payload)
        if params["event"] == "message_received":
            messages.put(json.loads(payload[0].decode()))

    s = session_type()
    log.info("%s", s)

    s.on_session_event = on_session_event
    s.on_event = on_event
    s.on_close = lambda: closed.put(True)
    s.on_conn_state = lambda state: log.debug("conn state: %s", state)
    s.on_conn_active = lambda: log.debug("conn active")
    s.set_params({"user_attrs": {"name": "ninchat-python"}, "message_types": ["*"]})
    s.open(lambda params: log.debug("open"))
    log.info("%s", s)

    action_id = s.send({"action": "describe_conn"})
    log.debug("action id: %d", action_id)

    user_id = user_ids.get()

    action_id = s.send({"action": "send_message", "message_type": "ninchat.com/text", "user_id": user_id}, [b'{ "text": "ok" }', b"more crap"])
    log.debug("action id: %d", action_id)

    msg = messages.get()
    s.close()
    closed.get()
    log.info("%s", s)
    log.info(msg["text"])


if __name__ == "__main__":
    test_client()
