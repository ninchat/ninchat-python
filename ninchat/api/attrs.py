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

"""Attributes for each entity type.

.. data:: user

   Dictionary; maps name strings to Attribute instances.

.. data:: identity

   Dictionary; maps name strings to Attribute instances.

.. data:: dialoguemember

   Dictionary; maps name strings to Attribute instances.

.. data:: channel

   Dictionary; maps name strings to Attribute instances.

.. data:: channelmember

   Dictionary; maps name strings to Attribute instances.

.. data:: realm

   Dictionary; maps name strings to Attribute instances.

.. data:: realmmember

   Dictionary; maps name strings to Attribute instances.

"""

from __future__ import absolute_import

from . import typechecks

class Attribute(object):
	"""Description of an entity attribute.

	.. attribute:: name

	   String

	.. attribute:: type

	   String

	.. attribute:: initable

	   Boolean

	.. attribute:: writable

	   Boolean

	.. attribute:: settable

	   Boolean

	.. attribute:: unsettable

	   Boolean

	"""
	def __init__(self, name, spec):
		self.name = name
		self.type = spec["type"]
		self.initable = spec.get("initable", False)
		self.writable = spec.get("writable", False)
		self.settable = spec.get("settable", self.writable)
		self.unsettable = spec.get("unsettable", self.writable)

	def __str__(self):
		return self.name

	def validate(self, value):
		"""Check if *value* conforms to the type requirements.
		"""
		return typechecks[self.type](value)

def init(root, dirname):
	import os, zipfile

	if os.path.isdir(root):
		dirpath = os.path.join(root, dirname)
		for name in os.listdir(dirpath):
			with open(os.path.join(dirpath, name)) as file:
				init_file(file, name)
	else:
		with zipfile.ZipFile(root) as zip:
			for name in zip.namelist():
				if os.path.dirname(name) == dirname:
					with zip.open(name) as file:
						init_file(file, name)

def init_file(file, name):
	import os
	from . import load_file

	if name.endswith(".json"):
		entity, _ = os.path.basename(name).rsplit(".", 1)
		globals()[entity] = load_file(file, Attribute)
