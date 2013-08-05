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

from __future__ import absolute_import

import json

from .. import api
from . import log

class Event(object):
	"""Holds an API event received from the server.  Event parameters may be
	accessed as instance attributes.  Optional parameters default to None.

	.. attribute:: payload

	   List of bytes objects.

	"""
	def __init__(self, frame):
		self._params = json.loads(frame.decode("utf-8"))
		self._length = self._params.pop("frames", 0)
		self.payload = []

	@property
	def type(self):
		"""String
		"""
		return self._params["event"]

	def __getattr__(self, name):
		spec = api.events[self.type].params[name]
		value = self._params.get(name)
		if value is None and spec.required:
			log.warning("event %r parameter %r is missing", event, name)
		return value

	def __str__(self):
		return self._params["event"]

	def __repr__(self):
		return "<Event %r %s%s>" % (
			self._params.get("event"),
			" ".join(
					"%s %r" % (k, v) for k, v in sorted(self._params.items())
					if k != "event"),
			(" payload " + " ".join(
					"%r" % p for p in self.payload)) if self.payload else "")
