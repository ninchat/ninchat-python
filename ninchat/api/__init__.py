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

"""Ninchat API metadata.

Module contents:
actions -- names-to-Interfaces dictionary
events -- names-to-Interfaces dictionary
Interface
Parameter
"""

try:
	# Python 2
	_ints = int, long
	_floats = int, long, float
	_strings = str, unicode
except NameError:
	# Python 3
	_ints = int
	_floats = int, float
	_strings = str

typechecks = {}

def declare_type(name):
	def decorator(checker):
		typechecks[name] = checker
		return checker

	return decorator

@declare_type("bool")
def is_bool(x):
	return isinstance(x, bool)

@declare_type("float")
def is_float(x):
	return isinstance(x, _floats)

@declare_type("int")
def is_int(x):
	return isinstance(x, _ints)

@declare_type("object")
def is_object(x):
	return isinstance(x, dict) and all(is_string(key) for key in x)

@declare_type("string")
def is_string(x):
	return isinstance(x, _strings)

@declare_type("string array")
def is_string_array(x):
	return isinstance(x, (list, tuple)) and all(is_string(item) for item in x)

@declare_type("time")
def is_time(x):
	return isinstance(x, _ints) and x >= 0

paramtypes = {}
actions = {}
events = {}

class Parameter(object):
	"""Description of an action/event parameter with name, type (string) and
	required (boolean) attributes.
	"""
	def __init__(self, key, spec):
		self.name = key
		self.required = spec

	@property
	def type(self):
		return paramtypes[self.name]

	def validate(self, x):
		"""Check if x conforms to the type requirements, or is None while the
		parameter is optional.
		"""
		return typechecks[self.type](x) or (x is None and not self.required)

class Interface(object):
	"""Description of an action or an event with name (string) and params
	(name-to-Parameter dictionary) attributes.
	"""
	def __init__(self, key, spec):
		self.name = key
		self.params = dict((k, Parameter(k, s)) for (k, s) in spec.items())

def load(root, name, cls, target):
	import os, zipfile

	if os.path.isdir(root):
		with open(os.path.join(root, name)) as file:
			load_file(file, cls, target)
	else:
		with zipfile.ZipFile(root) as zip:
			with zip.open(name) as file:
				load_file(file, cls, target)

def load_file(file, cls, target=None):
	import json

	if target is None:
		target = {}

	for key, spec in json.load(file).items():
		target[key] = cls(key, spec)

	return target

from . import attrs
from . import messages

def __init():
	from os.path import dirname, basename, join

	root = dirname(dirname(dirname(__file__)))
	pkg = dirname(__file__)[len(root)+1:]

	load(root, join(pkg, "spec/json/paramtypes.json"), (lambda key, spec: spec), paramtypes)
	load(root, join(pkg, "spec/json/actions.json"), Interface, actions)
	load(root, join(pkg, "spec/json/events.json"), Interface, events)
	attrs.init(root, join(pkg, "spec/json/attrs"))

__init()
