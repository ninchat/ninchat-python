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

from __future__ import absolute_import

import json
import time

from .. import api


class ParameterError(Exception):
    """Action is missing a required parameter or the parameter value is
    invalid.

    .. attribute:: param

       The associated ninchat.api.Parameter instance (if applicable).

    """

    def __init__(self, message, param=None):
        super(ParameterError, self).__init__(message)
        self.param = param


class Action(object):
    """Holds an action to be sent to the server.  `Parameters are
    action-specific <https://ninchat.com/api#actions>`_.  If supported by the
    action type, the payload should be a list of bytes objects.

    Note: reusing an Action instance isn't supported.
    """
    retry_count = 3
    retry_timeout = 15

    _transient_for_session_id = None
    _resend_num = 0
    _resend_time = None

    def __init__(self, name, payload=None, **params):
        assert "action" not in params

        self._params = params
        self.payload = payload or []

        specs = api.actions[name].params

        for key, spec in specs.items():
            value = self._params.get(key)
            if value is None:
                if spec.required:
                    raise ParameterError(
                        "%r is missing from %r action" % (key, name),
                        spec)
            else:
                if not spec.validate(value):
                    raise ParameterError(
                        "%r value is invalid in %r action: %r" %
                        (key, name, value),
                        spec)

        for key in self._params:
            if key not in specs:
                raise ParameterError(
                    "unknown %r in %r action" % (key, name))

        self._params["action"] = name

        if self.payload:
            self._params["frames"] = len(self.payload)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<Action %r %s%s>" % (
            self.name,
            " ".join("%s %r" % (k, v)
                     for k, v
                     in sorted(self._params.items())
                     if k not in ("action", "frames")),
            (" payload " + " ".join("%r" % p for p in self.payload)
             if self.payload
             else ""))

    def __lt__(self, other):
        if self._resend_time < other._resend_time:
            return True
        elif self._resend_time == other._resend_time:
            return id(self) < id(other)
        else:
            return False

    def __le__(self, other):
        if self._resend_time < other._resend_time:
            return True
        elif self._resend_time == other._resend_time:
            return id(self) <= id(other)
        else:
            return False

    def __gt__(self, other):
        if self._resend_time > other._resend_time:
            return True
        elif self._resend_time == other._resend_time:
            return id(self) > id(other)
        else:
            return False

    def __ge__(self, other):
        if self._resend_time > other._resend_time:
            return True
        elif self._resend_time == other._resend_time:
            return id(self) >= id(other)
        else:
            return False

    @property
    def _frames(self):
        return [json.dumps(self._params, separators=(",", ":"))] + self.payload

    def _set_event_id(self, event_id):
        if event_id is not None:
            self._params["event_id"] = event_id
        else:
            try:
                del self._params["event_id"]
            except KeyError:
                pass

    def _sent(self):
        self._resend_num += 1
        if self._resend_num >= self.retry_count:
            self._resend_time = None
            return False
        else:
            self._resend_time = time.time() + self.retry_timeout
            return True

    @property
    def name(self):
        """String (corresponds to the "action" parameter in the API
        specification).
        """
        return self._params["action"]

    @property
    def action_id(self):
        """Integer or None.
        """
        return self._params.get("action_id")

    @property
    def multiple_events(self):
        return self.name == "load_history"

    def get_pending_events(self, event):
        if self.multiple_events:
            return event._params.get("history_length", 0)
        else:
            return 0


class SessionAction(Action):

    def __init__(self, action, session_id=None, event_id=None):
        self._params = {"action": action}
        self.payload = []

        if session_id is not None:
            self._params["session_id"] = session_id

        if event_id is not None:
            self._params["event_id"] = event_id
