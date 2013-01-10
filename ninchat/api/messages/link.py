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

from . import log, Message, declare_messagetype
from .. import typechecks

@declare_messagetype("ninchat.com/link")
class LinkMessage(Message):
	"""Handler for ninchat.com/link messages.
	"""
	_specs = {
		"icon":      (typechecks["string"], True),
		"name":      (typechecks["string"], True),
		"size":      (typechecks["int"],    True),
		"thumbnail": (typechecks["string"], False),
		"url":       (typechecks["string"], True),
	}
	_valid = None
	_data = None

	def _decode(self):
		if self._valid is not None:
			return

		self._valid = False

		data = self._decode_json_header()
		if not isinstance(data, dict):
			log.warning("%s has no data", self.type)
			return

		for name, (checkfunc, required) in self._specs.iteritems():
			value = data.get(name)
			if value is not None:
				if not checkfunc(value):
					log.warning("%s %s is invalid", self.type, name)
					return
			elif required:
				log.warning("%s %s is missing", self.type, name)
				return

		if set(data.keys()) - set(self._specs.keys()):
			log.warning("%s entry contains extraneous properties", self.type)
			return

		self._valid = True
		self._data = data

	def validate(self):
		self._decode()
		return self._valid

	def stringify(self):
		return self.get_property("url") or ""

	def get_property(self, name):
		self._decode()
		if self._valid:
			return self._data.get(name)
