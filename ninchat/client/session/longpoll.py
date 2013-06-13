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

import http.client
import json
import queue
import ssl
import threading
import time
import urllib

from ninchat.client import log
from ninchat.client.event import Event

class Connection(object):

	path = "/poll/1"

	def __init__(self, session, action):
		self.session = session
		self.queue = queue.Queue(10)
		self.event_id = None
		self.sender = Sender(self)
		self.receiver = Receiver(self)

		self.queue.put(action)

	def connect(self):
		self.sender.thread.start()

	def send_action(self, action):
		self.queue.put(action)

	def modify_params(self, params):
		return params

class Half(object):

	def __init__(self, conn):
		self.conn = conn

		self.thread = threading.Thread(target=self.run)
		self.thread.daemon = True

		self._http = None

	def run(self):
		try:
			self.main()
		finally:
			if self._http:
				self._http.close()

	def call_params(self, params):
		if not self._http:
			context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
			context.verify_mode = ssl.CERT_REQUIRED
			context.set_default_verify_paths()
			self._http = http.client.HTTPSConnection(self.conn.session.session_host, context=context)

		params = self.conn.modify_params(params)
		data = json.dumps(params)
		url = self.conn.path + "?" + urllib.parse.urlencode({ "data": data, "callback": "_" })

		log.debug("longpoll %d %s: making %s request (session %s #%s)", id(self.conn.session), self.log_name, params["action"], params.get("session_id"), params.get("event_id"))

		resp = None
		try:
			self._http.request("GET", url)
			resp = self._http.getresponse()
		finally:
			if resp is None:
				h = self._http
				self._http = None
				h.close()

		return resp

	def call_action(self, action):
		params = action._params

		if "frames" in params:
			del params["frames"]
			params["payload"] = json.loads(action.payload[0])

		params["session_id"] = self.conn.session.session_id

		return self.call_params(params)

	def event_received(self, resp):
		event_id = None

		js = resp.read()

		log.debug("longpoll %d %s: response read", id(self.conn.session), self.log_name)

		if js.startswith(b"_(") and js.endswith(b");"):
			for data in json.loads(js[2:-2].decode("utf-8")):
				payload = data.get("payload")
				if payload is not None:
					del data["payload"]
					data["frames"] = 1

				eid = data.get("event_id")
				if eid is not None:
					event_id = eid

				event = Event(json.dumps(data).encode("utf-8"))

				if payload is not None:
					event.payload.append(json.dumps(payload))

				self.conn.session._received(event)
		else:
			log.error("response: %r", js)
			# TODO

		return event_id

# TODO: exponential back-off, and fail Connection after a while to revert to default session host

class Sender(Half):

	log_name = "sender"

	def main(self):
		action = self.conn.queue.get()

		# TODO: abort if signaled somehow
		while True:
			try:
				resp = self.call_action(action)
				break
			except http.client.HTTPException:
				log.exception("longpoll session creation")
				time.sleep(1)

		self.conn.event_id = self.event_received(resp)
		self.conn.receiver.thread.start()

		action = None

		while True:
			if action is None:
				action = self.conn.queue.get()
				if not action:
					break

			# TODO
			if str(action) == "resume_session":
				action = None
				continue

			try:
				resp = self.call_action(action)
				action = None
			except http.client.HTTPException:
				log.exception("longpoll action sending")
				time.sleep(1)
			else:
				self.event_received(resp)

class Receiver(Half):

	log_name = "receiver"

	def main(self):
		while self.conn.session.session_id is not None:
			try:
				params = { "action": "resume_session", "session_id": self.conn.session.session_id }
				if self.conn.event_id is not None:
					params["event_id"] = self.conn.event_id
				resp = self.call_params(params)
			except http.client.HTTPException:
				log.exception("longpoll event reception")
				time.sleep(1)
			else:
				self.conn.event_id = self.event_received(resp)

		self.conn.actions.put(None)
