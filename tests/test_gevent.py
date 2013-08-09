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

from ninchat.client.call import SyncQueueAdapter
from ninchat.client.gevent import QueueSession

from . import log

class State(object):

	def __init__(self, session_type):
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
				log.error("%d: %r", num, event)
				break
			elif event.name == "message_received":
				n = int(json.loads(event.payload[0])["text"])
				log.debug("%d: %s %s", num, n, event.message_id)
				gevent.spawn(self.send, n + 1)
			else:
				log.debug("%d: spurious: %r", num, event)

	def init(self):
		event = self.session.create(message_types=["ninchat.com/text"])
		if event is None or event.name == "error":
			log.error("create: %r", event)
			return

		self.user_id = event.user_id

	def send(self, n):
		event = self.session.send_message(user_id=self.other.user_id, message_type="ninchat.com/text", message_ttl=1, payload=[json.dumps({ "text": str(n) })])
		if event is None or event.name == "error":
			log.error("send_message: %r", event)
			return

def main(session_type=QueueSession):
	s1 = State(session_type)
	s2 = State(session_type)

	s1.other = s2
	s2.other = s1

	s1.send(0)

	try:
		gevent.joinall([s1.greenlet, s2.greenlet])
	except KeyboardInterrupt:
		pass

if __name__ == "__main__":
	main()
