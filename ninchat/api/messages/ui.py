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

from . import _AbstractObjectMessage, _AbstractObjectArrayMessage, declare_messagetype
from .. import is_object, is_string


def _is_string_in_list(x, strings=[]):
    return is_string(x) and x in strings


def _is_string_with_list(x, max_length=0):
    return is_string(x) and x.count(" ") < max_length


@declare_messagetype("ninchat.com/ui/action")
class ActionUIMessage(_AbstractObjectMessage):
    """Handler for ninchat.com/ui/action messages.
    """
    def __is_string_in_list(x):
        return _is_string_in_list(x, ActionUIMessage._valid_actions)

    _specs = {
        "action": (__is_string_in_list, True),
        "target": (is_object, True),
    }

    _valid_actions = ["click"]


@declare_messagetype("ninchat.com/ui/compose")
class ComposeUIMessage(_AbstractObjectArrayMessage):
    """Handler for ninchat.com/ui/action messages.
    """
    def __is_string_in_list(x):
        return _is_string_in_list(x, ComposeUIMessage._valid_elements)

    def __is_string_with_list(x):
        return _is_string_with_list(x, ComposeUIMessage._valid_class_list_max_length)

    _specs = {
        "class": (__is_string_with_list, False),
        "element": (__is_string_in_list, True),
        "id": (is_string, False),
        "label": (is_string, False),
        "name": (is_string, False),
    }

    _valid_class_list_max_length = 5
    _valid_elements = ["button"]
