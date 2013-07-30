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

import json
import sys

sys.path.insert(0, "")

import gevent

from ninchat.client.session.websocket.geventful import Session

from . import log

def handle(session, other_user_id):
	for num, event in enumerate(session):
		if event.type == "error":
			log.error("%d: %r", num, event)
			break
		elif event.type == "message_received":
			n = int(json.loads(event.payload[0])["text"])
			log.debug("%d: %s %s", num, n, event.message_id)
			session.send_message(action_id=None, user_id=other_user_id, message_type="ninchat.com/text", message_ttl=1, payload=[json.dumps({ "text": str(n + 1) })])
		else:
			log.debug("%d: %r", num, event)

def main(session_type=Session):
	s1 = session_type()
	s2 = session_type()

	s1.create(message_types=["ninchat.com/text"])
	s2.create(message_types=["ninchat.com/text"])

	e1 = s1.receive()
	if e1.type == "error":
		log.error("%r", e1)
		return

	e2 = s2.receive()
	if e2.type == "error":
		log.error("%r", e2)
		return

	s1.send_message(action_id=None, user_id=e2.user_id, message_type="ninchat.com/text", message_ttl=1, payload=[json.dumps({ "text": "0" })])

	g1 = gevent.spawn(handle, s1, e2.user_id)
	g2 = gevent.spawn(handle, s2, e1.user_id)

	try:
		gevent.joinall([g1, g2])
	except KeyboardInterrupt:
		pass

if __name__ == "__main__":
	main()
