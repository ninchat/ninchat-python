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

from __future__ import absolute_import

import json
import logging
import sys
import threading
import time

sys.path.insert(0, "")

from ninchat.client.legacy.adapter import AsyncCallbackAdapter
from ninchat.client.legacy.session.thread import CallbackSession, QueueSession

log = logging.getLogger("test")

opened_queue = QueueSession.queue_type(2)
closed_queue = QueueSession.queue_type(2)


class State(object):

    def __init__(self, num):
        self.num = num
        self.session = None
        self.other = None
        self.user_id = None
        self.error = False

    def _error(self, event):
        if event is None or event.name == "error":
            log.error("%d: %r", self.num, event)
            if not self.error:
                self.error = True
                closed_queue.put(self)
            return True

        return False

    def created(self, session, event):
        if not self._error(event):
            log.debug("%d: created: %r", self.num, event)
            self.user_id = event.user_id

        opened_queue.put(self)

    def message_sent(self, session, action, event):
        self._error(event)

    def spurious(self, session, event):
        if not self._error(event):
            if event.name == "message_received":
                s = event.payload[0]
                if isinstance(s, bytes):
                    s = s.decode("utf-8")
                n = int(json.loads(s)["text"])
                log.info("%d: %s %s", self.num, n, event.message_id)
                self.session.send_message(self.message_sent, user_id=self.other.user_id, message_type="ninchat.com/text", payload=[json.dumps({"text": str(n + 1)})])
            else:
                log.debug("%d: spurious: %r", self.num, event)

    def closed(self, session):
        log.debug("%d: closed", self.num)
        if not self.error:
            closed_queue.put(self)


def create(session_type, num):
    state = State(num)
    state.session = AsyncCallbackAdapter(session_type(state.spurious, state.closed))
    state.session.create(state.created, message_types=["ninchat.com/text"])
    return state


def main(session_type=CallbackSession):
    s1 = create(session_type, 1)
    s2 = create(session_type, 2)

    s1.other = s2
    s2.other = s1

    opened_queue.get()
    opened_queue.get()

    if s1.error or s2.error:
        return

    s1.session.send_message(s1.message_sent, user_id=s2.user_id, message_type="ninchat.com/text", payload=[json.dumps({"text": "0"})])

    try:
        closed_queue.get()
        closed_queue.get()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
