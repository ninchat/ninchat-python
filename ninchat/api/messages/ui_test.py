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

from . import factories

factory_dict = dict(factories)


def message_test(mtype, index, frame):
    factory = factory_dict[mtype]
    payload = [frame]
    message = factory(mtype, payload)
    assert message.validate()


def test_message_ui_action():
    for i, frame in enumerate([
        b'{"action": "click", "target": {"class": "x y z", "element": "a", "href": "https://example.net", "label": "x"}}',
        b'{"action": "click", "target": {"class": "x y z", "element": "button", "id": "x", "label": "x", "name": "x"}}',
        b'{"action": "click", "target": {"class": "x y z", "element": "button", "label": "x", "name": "x"}}',
        b'{"action": "click", "target": {"class": "x", "element": "button", "id": "x", "label": "x", "name": "x"}}',
        b'{"action": "click", "target": {"class": "x", "element": "button", "id": "x", "label": "x"}}',
        b'{"action": "click", "target": {"element": "a", "href": "https://example.net", "id": "x y z", "label": "x y z"}}',
        b'{"action": "click", "target": {"element": "a", "href": "https://example.net", "id": "x", "label": "x"}}',
        b'{"action": "click", "target": {"element": "a", "href": "https://example.net", "label": "x"}}',
        b'{"action": "click", "target": {"element": "a", "href": "https://example.net"}}',
        b'{"action": "click", "target": {"element": "button", "id": "x y z", "label": "x y z"}}',
        b'{"action": "click", "target": {"element": "button", "id": "x", "label": "x y z"}}',
        b'{"action": "click", "target": {"element": "button", "id": "x", "label": "x"}}',
        b'{"action": "click", "target": {"element": "button", "id": "x"}}',
        b'{"action": "click", "target": {"element": "button", "label": "x", "name": "x"}}',
        b'{"action": "click", "target": {"element": "button", "label": "x"}}',
    ]):
        message_test("ninchat.com/ui/action", i, frame)


def test_message_ui_compose():
    for i, frame in enumerate([
        b'[]',
        b'[{"class": "x y z", "element": "a", "href": "https://example.net", "id": null, "label": "x", "name": null}, {"class": "x y z", "element": "a", "href": "https://example.net", "id": null, "label": "x", "name": null}]',
        b'[{"class": "x y z", "element": "button", "id": "x", "label": "x", "name": "x"}, {"class": "x y z", "element": "button", "label": "x", "name": "x"}]',
        b'[{"class": "x", "element": "button", "id": "x", "label": "x y z", "name": "x"}, {"class": "x", "element": "button", "id": "x", "label": "x y z", "name": "x"}]',
        b'[{"class": "x", "element": "button", "id": "x", "label": "x", "name": "x"}, {"class": "x", "element": "button", "id": "x", "label": "x", "name": "x"}]',
        b'[{"class": "x", "element": "button", "id": "x", "label": "x", "name": "x"}]',
        b'[{"element": "a", "href": "https://example.net", "id": "x y z", "label": "x y z"}, {"element": "a", "href": "https://example.net", "id": "x y z", "label": "x y z"}]',
        b'[{"element": "a", "href": "https://example.net", "id": "x y z", "label": "x y z"}, {"element": "button", "id": "x y z", "label": "x y z"}]',
        b'[{"element": "a", "href": "https://example.net", "id": "x y z", "label": "x y z"}]',
        b'[{"element": "a", "href": "https://example.net", "id": "x", "label": "x"}, {"element": "a", "href": "https://example.net", "id": "x y z", "label": "x y z"}]',
        b'[{"element": "a", "href": "https://example.net", "id": "x", "label": "x"}, {"element": "button", "id": "x y z", "label": "x y z"}]',
        b'[{"element": "a", "href": "https://example.net", "id": "x", "label": "x"}]',
        b'[{"element": "a", "href": "https://example.net", "label": "x"}, {"element": "a", "href": "https://example.net", "label": "x"}]',
        b'[{"element": "a", "href": "https://example.net", "label": "x"}]',
        b'[{"element": "a", "href": "https://example.net"}]',
        b'[{"element": "button", "id": "x y z", "label": "x y z"}, {"element": "a", "href": "https://example.net", "id": "x y z", "label": "x y z"}]',
        b'[{"element": "button", "id": "x y z", "label": "x y z"}, {"element": "button", "id": "x y z", "label": "x y z"}]',
        b'[{"element": "button", "id": "x y z", "label": "x y z"}, {"element": "button", "id": "x", "label": "x"}]',
        b'[{"element": "button", "id": "x y z", "label": "x y z"}]',
        b'[{"element": "button", "id": "x", "label": ""}, {"element": "button", "id": "x", "label": ""}]',
        b'[{"element": "button", "id": "x", "label": ""}, {"element": "button", "id": "x", "label": "x"}]',
        b'[{"element": "button", "id": "x", "label": "x y z"}, {"element": "button", "id": "x", "label": "x y z"}]',
        b'[{"element": "button", "id": "x", "label": "x y z"}, {"element": "button", "id": "x", "label": "x"}]',
        b'[{"element": "button", "id": "x", "label": "x y z"}]',
        b'[{"element": "button", "id": "x", "label": "x"}, {"class": "x", "element": "button", "id": "x", "label": "x"}]',
        b'[{"element": "button", "id": "x", "label": "x"}, {"element": "button", "id": "x y z", "label": "x y z"}]',
        b'[{"element": "button", "id": "x", "label": "x"}, {"element": "button", "id": "x", "label": ""}]',
        b'[{"element": "button", "id": "x", "label": "x"}, {"element": "button", "id": "x", "label": "x y z"}]',
        b'[{"element": "button", "id": "x", "label": "x"}, {"element": "button", "id": "x", "label": "x"}]',
        b'[{"element": "button", "id": "x", "label": "x"}]',
        b'[{"element": "button", "label": "x", "name": "x"}]',
        b'[{"element": "button", "label": "x"}, {"element": "button", "label": "x"}]',
    ]):
        message_test("ninchat.com/ui/compose", i, frame)
