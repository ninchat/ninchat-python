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

"""Standard message type definitions.

log -- a logging.Logger which may be configured by the application
factories -- list of message-type-pattern/handler-factory pairs
Message -- message handler interface

A handler factory takes message type and payload, and returns a Message
implementation or None.
"""

import logging

log = logging.getLogger("ninchat.api.messages")
factories = []

class Message(object):
	"""Contains the type and payload attributes.  Subclasses should override
	the validate(), stringify() and get_property(name) methods if
	applicable.
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

def declare_messagetype(pattern):
	def decorator(factory):
		factories.append((pattern, factory))
		return factory
	return decorator

from . import info
from . import text
