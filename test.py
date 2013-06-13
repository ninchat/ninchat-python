#!/usr/bin/env python3

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

import json
import logging
import queue
import sys
import threading
import time

sys.path.insert(0, "")

import ninchat.client

log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
log = logging.getLogger("test")
log.addHandler(log_handler)
log.setLevel(logging.DEBUG)

ninchat.client.log.addHandler(log_handler)
ninchat.client.log.setLevel(logging.DEBUG)

opened_queue = queue.Queue(2)
closed_queue = queue.Queue(2)

class Session(ninchat.client.ThreadedSession):

	def __init__(self, num):
		self.num = num
		self.user_id = None
		self.error = False
		super(Session, self).__init__()

	def received(self, event):
		if event.type == "error":
			log.error("%d: %r", self.num, event)
			self.error = True
			closed_queue.put(self)
			if self.user_id is None:
				opened_queue.put(self)
		elif event.type == "session_created":
			self.user_id = event.user_id
			opened_queue.put(self)
		elif event.type == "message_received":
			n = int(json.loads(event.payload[0])["text"])
			log.debug("%d: %s %s", self.num, n, event.message_id)
			self.send_message(action_id=None, user_id=self.other.user_id, message_type="ninchat.com/text", message_ttl=1, payload=[json.dumps({ "text": str(n + 1) })])
		else:
			log.debug("%d: %r", self.num, event)

	def closed(self):
		log.debug("session closed")
		if not self.error:
			closed_queue.put(self)

def main(session_type=Session):
	s1 = session_type(1)
	s2 = session_type(2)

	s1.other = s2
	s2.other = s1

	s1.create(message_types=["ninchat.com/text"])
	s2.create(message_types=["ninchat.com/text"])

	opened_queue.get()
	opened_queue.get()

	if s1.error or s2.error:
		return

	s1.send_message(action_id=None, user_id=s2.user_id, message_type="ninchat.com/text", message_ttl=1, payload=[json.dumps({ "text": "0" })])

	try:
		closed_queue.get()
		closed_queue.get()
	except KeyboardInterrupt:
		pass

if __name__ == "__main__":
	main()
