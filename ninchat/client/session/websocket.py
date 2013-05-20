# Copyright (c) 2012-2013, Somia Reality Oy
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

import ws4py.client.threadedclient

from ninchat.client.event import Event

class Connection(ws4py.client.threadedclient.WebSocketClient):
	url_format = "wss://{}/socket"
	protocol = "ninchat.com-1"

	def __init__(self, session, action):
		super(Connection, self).__init__(
				self.url_format.format(session.session_host),
				[self.protocol])

		self.session = session
		self.action = action
		self.event = None

	def send_action(self, action):
		for frame in action.frames:
			self.send(frame)

	def opened(self):
		self.send_action(self.action)
		del self.action

	def received_message(self, message):
		frame = message.data
		event = self.event
		if event:
			event.payload.append(frame)
			if len(event.payload) >= event._length:
				self.event = None
				self.session._received(event)
		elif frame:
			event = Event(frame)
			if event._length > 0:
				self.event = event
			else:
				self.session._received(event)

	def closed(self, code, reason):
		self.session._disconnected()
