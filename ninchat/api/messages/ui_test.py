# Copyright (c) 2019, Somia Reality Oy
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

import json

from . import factories

factory_dict = dict(factories)


def message_test(mtype, index, data):
    factory = factory_dict[mtype]
    payload = [json.dumps(data).encode()]
    message = factory(mtype, payload)
    assert message.validate()


def test_message_ui_action():
    for i, data in enumerate([
        {"action": "click", "target": {"class": "x y z", "element": "a", "href": "https://example.net", "label": "x"}},
        {"action": "click", "target": {"class": "x y z", "element": "button", "id": "x", "label": "x", "name": "x"}},
        {"action": "click", "target": {"class": "x y z", "element": "button", "label": "x", "name": "x"}},
        {"action": "click", "target": {"class": "x", "element": "button", "id": "x", "label": "x", "name": "x"}},
        {"action": "click", "target": {"class": "x", "element": "button", "id": "x", "label": "x"}},
        {"action": "click", "target": {"element": "a", "href": "https://example.net", "id": "x y z", "label": "x y z"}},
        {"action": "click", "target": {"element": "a", "href": "https://example.net", "id": "x", "label": "x"}},
        {"action": "click", "target": {"element": "a", "href": "https://example.net", "label": "x"}},
        {"action": "click", "target": {"element": "a", "href": "https://example.net"}},
        {"action": "click", "target": {"element": "button", "id": "x y z", "label": "x y z"}},
        {"action": "click", "target": {"element": "button", "id": "x", "label": "x y z"}},
        {"action": "click", "target": {"element": "button", "id": "x", "label": "x"}},
        {"action": "click", "target": {"element": "button", "id": "x"}},
        {"action": "click", "target": {"element": "button", "label": "x", "name": "x"}},
        {"action": "click", "target": {"element": "button", "label": "x"}},
    ]):
        message_test("ninchat.com/ui/action", i, data)


def test_message_ui_compose():
    for i, data in enumerate([
        [],
        [{"class": "x y z", "element": "a", "href": "https://example.net", "id": None, "label": "x", "name": None}, {"class": "x y z", "element": "a", "href": "https://example.net", "id": None, "label": "x", "name": None}],
        [{"class": "x y z", "element": "button", "id": "x", "label": "x", "name": "x"}, {"class": "x y z", "element": "button", "label": "x", "name": "x"}],
        [{"class": "x", "element": "button", "id": "x", "label": "x y z", "name": "x"}, {"class": "x", "element": "button", "id": "x", "label": "x y z", "name": "x"}],
        [{"class": "x", "element": "button", "id": "x", "label": "x", "name": "x"}, {"class": "x", "element": "button", "id": "x", "label": "x", "name": "x"}],
        [{"class": "x", "element": "button", "id": "x", "label": "x", "name": "x"}],
        [{"element": "a", "href": "https://example.net", "id": "x y z", "label": "x y z"}, {"element": "a", "href": "https://example.net", "id": "x y z", "label": "x y z"}],
        [{"element": "a", "href": "https://example.net", "id": "x y z", "label": "x y z"}, {"element": "button", "id": "x y z", "label": "x y z"}],
        [{"element": "a", "href": "https://example.net", "id": "x y z", "label": "x y z"}],
        [{"element": "a", "href": "https://example.net", "id": "x", "label": "x"}, {"element": "a", "href": "https://example.net", "id": "x y z", "label": "x y z"}],
        [{"element": "a", "href": "https://example.net", "id": "x", "label": "x"}, {"element": "button", "id": "x y z", "label": "x y z"}],
        [{"element": "a", "href": "https://example.net", "id": "x", "label": "x"}],
        [{"element": "a", "href": "https://example.net", "label": "x"}, {"element": "a", "href": "https://example.net", "label": "x"}],
        [{"element": "a", "href": "https://example.net", "label": "x"}],
        [{"element": "a", "href": "https://example.net"}],
        [{"element": "button", "id": "x y z", "label": "x y z"}, {"element": "a", "href": "https://example.net", "id": "x y z", "label": "x y z"}],
        [{"element": "button", "id": "x y z", "label": "x y z"}, {"element": "button", "id": "x y z", "label": "x y z"}],
        [{"element": "button", "id": "x y z", "label": "x y z"}, {"element": "button", "id": "x", "label": "x"}],
        [{"element": "button", "id": "x y z", "label": "x y z"}],
        [{"element": "button", "id": "x", "label": ""}, {"element": "button", "id": "x", "label": ""}],
        [{"element": "button", "id": "x", "label": ""}, {"element": "button", "id": "x", "label": "x"}],
        [{"element": "button", "id": "x", "label": "x y z"}, {"element": "button", "id": "x", "label": "x y z"}],
        [{"element": "button", "id": "x", "label": "x y z"}, {"element": "button", "id": "x", "label": "x"}],
        [{"element": "button", "id": "x", "label": "x y z"}],
        [{"element": "button", "id": "x", "label": "x"}, {"class": "x", "element": "button", "id": "x", "label": "x"}],
        [{"element": "button", "id": "x", "label": "x"}, {"element": "button", "id": "x y z", "label": "x y z"}],
        [{"element": "button", "id": "x", "label": "x"}, {"element": "button", "id": "x", "label": ""}],
        [{"element": "button", "id": "x", "label": "x"}, {"element": "button", "id": "x", "label": "x y z"}],
        [{"element": "button", "id": "x", "label": "x"}, {"element": "button", "id": "x", "label": "x"}],
        [{"element": "button", "id": "x", "label": "x"}],
        [{"element": "button", "label": "x", "name": "x"}],
        [{"element": "button", "label": "x"}, {"element": "button", "label": "x"}],
        [{"element": "select", "options": [{"label": "x", "value": "x"}]}],
        [{"element": "select", "options": [{"label": "x", "value": "x"}, {"label": "y", "value": "y"}]}],
    ]):
        message_test("ninchat.com/ui/compose", i, data)
