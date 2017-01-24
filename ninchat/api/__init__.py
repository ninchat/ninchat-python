# Copyright (c) 2012-2017, Somia Reality Oy
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

"""Python data structures describing various aspects of the api.ninchat.com
service.

.. data:: actions

   Dictionary; maps name strings to Interface instances.

.. data:: events

   Dictionary; maps name strings to Interface instances.

.. data:: paramtypes

   Dictionary; maps name strings to Parameter instances.

.. data:: objecttypes

   Dictionary; maps name strings to Object instances.

"""

from __future__ import absolute_import

try:
    from typing import Any, Dict, Tuple
except ImportError:
    pass

# Python 3
_ints = int           # type: type
_floats = int, float  # type: Tuple[type, type]
_strings = str        # type: type

try:
    # Python 2
    _ints = int, long           # type: ignore
    _floats = int, long, float  # type: ignore
    _strings = str, unicode     # type: ignore
except NameError:
    pass

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


paramtypes = {}   # type: Dict[str, Any]
objecttypes = {}  # type: Dict[str, Object]
actions = {}      # type: Dict[str, Interface]
events = {}       # type: Dict[str, Interface]


class Parameter(object):
    """Description of an action's or an event's parameter.

    .. attribute:: name

       String

    .. attribute:: type

       String|None

    .. attribute:: required

       Boolean

    """

    def __init__(self, key, spec):
        self.name = key

        if isinstance(spec, bool):
            self.type = paramtypes[self.name]
            self.required = spec
        else:
            self.type = spec.get("type")
            self.required = not spec.get("optional", False)

    def validate(self, value):
        """Check if *value* conforms to the type requirements, or is None while
        the parameter is optional.
        """
        return typechecks[self.type](value) or (value is None and not self.required)


class Object(object):
    """Description of an event parameter's structure.

    .. attribute:: name

       String

    .. attribute:: value

       String|None; type of a map object's values.

    .. attribute:: item

       String|None; type of an array object's items.

    .. attribute:: params

       Dictionary|None; maps property name strings to Parameter instances.

    """

    def __init__(self, key, spec):
        self.name = key
        self.value = spec.get("value")
        self.item = spec.get("item")
        self.params = None

        paramspecs = spec.get("params")
        if paramspecs is not None:
            self.params = {}
            for name, spec in paramspecs.items():
                self.params[name] = Parameter(name, spec)


class Interface(object):
    """Description of an action or an event.

    .. attribute:: name

       String

    .. attribute:: params

       Dictionary; maps name strings to Parameter instances.

    """

    def __init__(self, key, spec):
        self.name = key
        self.params = dict((k, Parameter(k, s)) for (k, s) in spec.items())


def load(root, name, cls, target):
    import os
    import zipfile

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
    from os.path import dirname, join, realpath

    filename = realpath(__file__)
    root = dirname(dirname(dirname(filename)))
    pkg = dirname(filename)[len(root)+1:]

    load(root, join(pkg, "spec/json/paramtypes.json"), (lambda key, spec: spec), paramtypes)
    load(root, join(pkg, "spec/json/objecttypes.json"), Object, objecttypes)
    load(root, join(pkg, "spec/json/actions.json"), Interface, actions)
    load(root, join(pkg, "spec/json/events.json"), Interface, events)
    attrs.init(root, join(pkg, "spec/json/attrs"))


__init()

# avoid warnings
attrs
messages
