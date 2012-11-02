# Copyright (c) 2012, Somia Reality Oy
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

from . import log, Message, declare_messagetype

try:
	# Python 2
	_string = unicode
	def _decode(x):
		return unicode(str(x), "utf-8")
except NameError:
	# Python 3
	_string = str
	def _decode(x):
		return str(x, "utf-8")

@declare_messagetype("ninchat.com/text")
class TextMessage(Message):
	"""Handler for ninchat.com/text messages.  Supports the "text" property.
	"""
	_valid = None
	_text = None

	def _decode(self):
		if self._valid is not None:
			return

		self._valid = False

		try:
			text = json.loads(_decode(self.payload[0]))["text"]
		except:
			log.warning("%s decoding failed", self.type, exc_info=True)
			return

		if isinstance(text, _string):
			self._valid = True
			self._text = text

	def validate(self):
		self._decode()
		return self._valid

	def stringify(self):
		self._decode()
		return self._text or ""

	def get_property(self, name):
		if name == "text":
			return self.stringify()
