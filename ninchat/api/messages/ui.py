# Copyright (c) 2017, Somia Reality Oy
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

from ninchat.api import is_object, is_string, is_url

from . import _AbstractObjectArrayMessage, _AbstractObjectMessage, _check_object, declare_messagetype

_action_action_specs = {
    "click": None,
}


def _is_action_action(x):
    return _check_object(_action_action_specs, x)


@declare_messagetype("ninchat.com/ui/action")
class ActionUIMessage(_AbstractObjectMessage):
    """Handler for ninchat.com/ui/action messages.
    """
    _specs = {
        "action": (_is_action_action, True),
        "target": (is_object, True),
    }


_compose_element_specs = {
    "a": {
        "href": (is_url, False),
        "target": (is_string, False),
    },
    "button": None,
}

_compose_option_specs = {
    "label": (is_string, True),
    "value": (is_string, True),
}


def _is_compose_class(x):
    return is_string(x) and x.count(" ") < 5


def _is_compose_element(x):
    return x == "select" or _check_object(_compose_element_specs, x)


def _is_compose_options(x):
    return isinstance(x, list) and len(x) in range(1, 20 + 1) and all(_is_compose_option(y) for y in x)


def _is_compose_option(y):
    return _check_object(_compose_option_specs, y)


@declare_messagetype("ninchat.com/ui/compose")
class ComposeUIMessage(_AbstractObjectArrayMessage):
    """Handler for ninchat.com/ui/action messages.
    """
    _specs = {
        "class": (_is_compose_class, False),
        "element": (_is_compose_element, True),
        "id": (is_string, False),
        "label": (is_string, False),
        "name": (is_string, False),
    }

    def _verify(self, data):
        if _check_object(self._specs, data) and (data.get("element") == "select") == ("options" in data):
            return data
        else:
            return None
