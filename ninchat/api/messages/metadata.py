# Copyright (c) 2015, Somia Reality Oy
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

from . import _AbstractObjectMessage, declare_messagetype, log
from .. import is_float, is_object, is_string

def _is_time(x):
	return is_float(x) and x > 0

@declare_messagetype("ninchat.com/metadata")
class MetadataMessage(_AbstractObjectMessage):
	"""Handler for ninchat.com/metadata messages.
	"""
	_specs = {
		"data": (is_object, True),
		"time": (_is_time,  False),
	}

	def _decode(self):
		data = _AbstractObjectMessage._decode(self)
		if data is None:
			return

		for v in data["data"].values():
			if not is_string(v):
				log.warning("%s values must be strings", self.type)
				return None

		return data

	def stringify(self):
		entries = []

		if self.validate():
			for i in self._data["data"].items():
				entries.append("%s: %s" % i)

		return "\n".join(entries)