# Copyright (c) 2012-2015, Somia Reality Oy
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

"""Standard message type definitions.

.. data:: log

   A logging.Logger instance which may be configured by the application.

.. data:: factories

   List of pairs; maps message-type-pattern strings to handler-factory
   callables.

   A handler-factory callable takes a message-type string and a payload list as
   positional parameters, and returns an instance of a Message implementation
   or None.

"""

from __future__ import absolute_import

import json
import logging

try:
	# Python 2
	def _decode(x):
		return unicode(str(x), "utf-8")
except NameError:
	# Python 3
	def _decode(x):
		return str(x, "utf-8")

log = logging.getLogger("ninchat.api.messages")
factories = []

class Message(object):
	"""Message handler interface.  Subclasses should override the validate(),
	stringify() and get_property(name) methods if applicable.

	.. attribute:: type

	   String

	.. attribute:: payload

	   List of some kind of objects.

	"""
	def __init__(self, messagetype, payload):
		self.type = messagetype
		self.payload = payload

	def validate(self):
		"""Check if the payload conforms to the type requirements.
		"""
		return False

	def stringify(self):
		"""Get the presentable textual content of the message, if any.
		"""
		return ""

	def get_property(self, name):
		"""Get a type-specific string property.
		"""
		return None

	def _decode_json_header(self):
		try:
			return json.loads(_decode(self.payload[0]))
		except:
			log.warning("%s decoding failed", self.type, exc_info=True)

class _AbstractObjectMessage(Message):
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

		for name, (checkfunc, required) in self._specs.items():
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
		return ""

	def get_property(self, name):
		self._decode()
		if self._valid:
			return self._data.get(name)

def declare_messagetype(pattern):
	def decorator(factory):
		factories.append((pattern, factory))
		return factory
	return decorator

from . import file
from . import info
from . import link
from . import metadata
from . import notice
from . import text
