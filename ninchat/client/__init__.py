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

""  # Enables documentation generation.

from __future__ import absolute_import

__all__ = ["Session", "Error"]

try:
    # Python 2
    xrange

    def _decode_str(x):
        return unicode(str(x), "utf-8")
except NameError:
    # Python 3
    xrange = range

    def _decode_str(x):
        return str(x, "utf-8")

import json
import logging

from _ninchat_cffi import ffi, lib

log = logging.getLogger(__name__)

_live = set()


class Error(Exception):
    """Raised by some Session methods."""
    pass


class Session(object):
    """Actions may be sent via the send() method.

    A server session must be established by configuring callbacks,
    calling the set_params() and open() methods, and waiting for a
    "session_created" (or an "error") event.  If the server drops the
    session (due to network timeout or some other exceptional reason), a
    new server session is created automatically, and another
    "session_created" event is delivered.

    Callbacks (the attributes prefixed with "on") may either be
    configured by setting them as properties, or by subclassing Session
    and implementing them as methods.

    Action/event params are dictionaries of string keys and arbitrary
    values.  Action/event payloads are lists of bytes-like objects.  See
    https://ninchat.com/api/v2 for details.

    Threading:

    - The API is not thread-safe.  If Session methods are invoked on
      multiple threads (probably a bad idea), proper synchronization
      must be taken care of.
    - The callbacks are executed on arbitrary threads, so proper
      synchronization must be taken care of.  (The asyncio and gevent
      implementations avoid this problem.)

    .. attribute:: on_session_event

       Session creation/failure callback.  Invoked with the event's
       params.  If an "error" event is delivered, it means that a new
       server session cannot be created automatically; the set_params()
       method must be used to update login credentials.  The close()
       method must be called if the session will not be resumed after an
       error.

    .. attribute:: on_event

       Event delivery callback.  Invoked with the event's params,
       event's payload, and a boolean which indicates if it was the last
       reply to the action indicated by the event's "action_id"
       parameter.

    .. attribute:: on_close

       Indicates that the session closure initiated by calling the
       close() method has completed.  Invoked without arguments.

    .. attribute:: on_conn_state

       Indicates a change in the internal connection state.  Invoked
       with one of the strings: "connecting", "connected", "disconnected".

    .. attribute:: on_active

       Indicates that there has recently been activity on the connection.
       Invoked without arguments.
"""

    on_session_event = None  # type: Callback[[Dict[str,Any]], None]
    on_event = None          # type: Callback[[Dict[str,Any], List[bytes], bool], None]
    on_close = None          # type: Callback[[], None]
    on_conn_state = None     # type: Optional[Callback[[str], None]]
    on_conn_active = None    # type: Optional[Callback[[], None]]

    _new_session = lib.new_common_session

    def __init__(self):
        # type: () -> None
        self.revision = 0
        self.state = "uninitialized"

        self._on_open = None
        self._on_replies = {}
        self._ctx = ffi.new_handle(self)
        self._internal = self._new_session(self._ctx)

    def __del__(self):
        lib.ninchat_session_delete(self._internal)

    def __str__(self):
        return "<{} {}.{}: {}>".format(type(self).__name__, self._internal, self.revision, self.state)

    def set_params(self, params):
        # type: (Dict[str,Any]) -> None
        """Sets or replaces the params to be used for the next
        "create_session" action."""
        assert self._ctx

        params_json = json.dumps(params).encode()
        params_ptr = ffi.from_buffer(params_json)
        params_len = len(params_json)

        lib.ninchat_session_set_params(self._internal, params_ptr, params_len)

    def open(self, on_open=None):
        # type: (Callable[[Dict[str,Any]], None]) -> None
        """Create a session on the server.  If specified, the on_open
        callback will be called with the (initial) session
        creation/failure event's params."""
        assert self._ctx
        assert self._ctx not in _live
        assert not self._on_open

        lib.ninchat_session_open(self._internal)

        self._on_open = on_open
        self.state = "initialized"

        _live.add(self._ctx)

    def close(self):
        # type: () -> None
        """Close the session on the server."""
        assert self._ctx in _live

        lib.ninchat_session_close(self._internal)
        self.state = "closing"

    def send(self, params, payload=None, on_reply=None):
        # type: (Dict[str,Any], Optional[Sequence[ByteString]], Optional[Callable[[Dict[str,Any], List[bytes], bool], None]]) -> None
        """Send an action.  If specified, the on_reply callback will be
        invoked with the reply event(s).  If the session is closed
        before the final reply event is received, the callback will be
        invoked with params set to None."""
        assert self._ctx in _live

        params_json = json.dumps(params).encode()
        params_ptr = ffi.from_buffer(params_json)
        params_len = len(params_json)

        payload_len = len(payload) if payload else 0
        payload_ptr = ffi.new("ninchat_frame[]", payload_len)
        for i in xrange(payload_len):
            frame = payload[i]
            lib.set_payload_frame(payload_ptr, i, ffi.from_buffer(frame), len(frame))

        action_id_ptr = ffi.new("int64_t *")

        error_ptr = lib.ninchat_session_send(self._internal, params_ptr, params_len, payload_ptr, payload_len, action_id_ptr)
        if error_ptr:
            try:
                error_str = ffi.string(error_ptr).decode()
            finally:
                lib.free(error_ptr)
            raise Error(error_str)

        action_id = ffi.unpack(action_id_ptr, 1)[0]
        if action_id and on_reply:
            self._on_replies[action_id] = on_reply

        return action_id

    def _handle_session_event(self, params):
        self.revision += 1

        try:
            if self._on_open and params.get("event") == "session_created":
                on_open = self._on_open
                self._on_open = None
                try:
                    on_open(params)
                except Exception:
                    log.exception("raised by session create callback")
        finally:
            self.on_session_event(params)

    def _handle_event(self, params, payload, last_reply):
        if last_reply:
            lookup = self._on_replies.pop
        else:
            lookup = self._on_replies.__getitem__

        try:
            try:
                on_reply = lookup(params["action_id"])
            except KeyError:
                pass
            else:
                try:
                    on_reply(params, payload, last_reply)
                except Exception:
                    log.exception("raised by action reply callback")
        finally:
            self.on_event(params, payload, last_reply)

    def _handle_close(self):
        _live.remove(self._ctx)
        self._ctx = None

        self.state = "closed"

        try:
            if self._on_open:
                try:
                    self._on_open(None)
                except Exception:
                    log.exception("raised by session create callback when session closed")

            for on_reply in self._on_replies.values():
                try:
                    on_reply(None, None, True)
                except Exception:
                    log.exception("raised by action reply callback when session closed")
        finally:
            if self.on_close:
                self.on_close()

    def _handle_conn_state(self, state):
        self.state = state
        if self.on_conn_state:
            self.on_conn_state(state)

    def _handle_conn_active(self):
        if self.on_conn_active:
            self.on_conn_active()

    def _handle_log(self, msg):
        log.debug("session %s.%s: %s", self._internal, self.revision, msg)

    def _call(self, call, *args):
        try:
            call(*args)
        except Exception:
            log.exception("raised by callback")


@ffi.def_extern()
def callback_session_event(ctx, params_ptr, params_len):
    session = ffi.from_handle(ctx)
    params = json.loads(_decode_str(ffi.buffer(params_ptr, params_len)))
    session._call(session._handle_session_event, params)


@ffi.def_extern()
def callback_event(ctx, params_ptr, params_len, payload_ptr, payload_len, last_reply_int):
    session = ffi.from_handle(ctx)
    params = json.loads(_decode_str(ffi.buffer(params_ptr, params_len)))
    payload = []
    for i in xrange(payload_len):
        frame = lib.payload_frame(payload_ptr, i)
        payload.append(ffi.string(lib.frame_data(frame), lib.frame_size(frame)))
    last_reply = (last_reply_int != 0)
    session._call(session._handle_event, params, payload, last_reply)


@ffi.def_extern()
def callback_close(ctx):
    session = ffi.from_handle(ctx)
    session._call(session._handle_close)


@ffi.def_extern()
def callback_conn_state(ctx, state_ptr):
    session = ffi.from_handle(ctx)
    state = ffi.string(state_ptr).decode()
    session._call(session._handle_conn_state, state)


@ffi.def_extern()
def callback_conn_active(ctx):
    session = ffi.from_handle(ctx)
    session._call(session._handle_conn_active)


@ffi.def_extern()
def callback_log(ctx, msg_ptr, msg_len):
    session = ffi.from_handle(ctx)
    msg = _decode_str(ffi.buffer(msg_ptr, msg_len))
    session._call(session._handle_log, msg)


del callback_session_event
del callback_event
del callback_close
del callback_conn_state
del callback_conn_active
del callback_log
