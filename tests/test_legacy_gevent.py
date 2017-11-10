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

from __future__ import absolute_import, unicode_literals

import gevent.monkey
gevent.monkey.patch_all()

import json
import logging
import sys

sys.path.insert(0, "")

import gevent

from ninchat.client.legacy.adapter import SyncQueueAdapter
from ninchat.client.legacy.session.gevent import QueueSession

log = logging.getLogger("test")

NUM_MESSAGES = 100


class State(object):

    def __init__(self, name, session_type):
        self.name = name
        self.session = SyncQueueAdapter(session_type())
        self.greenlet = gevent.spawn(self.loop)

        event = self.session.create(message_types=["ninchat.com/text"])
        if event is None or event.name == "error":
            log.error("create: %r", event)
            return

        self.user_id = event.user_id

    def loop(self):
        for num, event in enumerate(self.session):
            if event.name == "error":
                log.error("%s%d: %r", self.name, num, event)
                break
            elif event.name == "message_received":
                n = int(json.loads(event.payload[0].decode())["text"])
                log.info("%s%d: %s %s", self.name, num, n, event.message_id)
                gevent.spawn(self.send, n + 1)
                if n >= NUM_MESSAGES - 1:
                    break
            else:
                log.debug("%s%d: spurious: %r", self.name, num, event)

    def send(self, n):
        event = self.session.send_message(user_id=self.other.user_id, message_type="ninchat.com/text", message_ttl=1, payload=[json.dumps({"text": str(n)})])
        if event is None or event.name == "error":
            log.error("%s: send_message: %r", self.name, event)
            return


def main(session_type=QueueSession):
    a = State("a", session_type)
    b = State("b", session_type)

    a.other = b
    b.other = a

    a.send(1)

    try:
        gevent.joinall([a.greenlet, b.greenlet])
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
