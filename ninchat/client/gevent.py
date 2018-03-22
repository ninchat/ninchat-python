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

__all__ = ["Session"]

import fcntl
import logging
import os
from time import time

import gevent
from gevent.fileobject import FileObject

from _ninchat_cffi import ffi, lib

from . import Session as BaseSession

log = logging.getLogger(__name__)

poll_duration = 1
poll_interval = 0.1


def _create_pipe():
    """Creates a readable co-operative (gevent) file-like object
    and a writable non-blocking raw file descriptor."""
    try:
        # Python 3, Linux
        r, w = os.pipe2(os.O_NONBLOCK | os.O_CLOEXEC)
    except AttributeError:
        r, w = os.pipe()
        fcntl.fcntl(w, fcntl.F_SETFL, fcntl.fcntl(w, fcntl.F_GETFL) | os.O_NONBLOCK)
    return FileObject(r, "rb"), w


_wakeup_recv_file, _wakeup_send_fd = _create_pipe()
_wakeup_send_time = 0

_heartbeat_init = False

_pending_calls = []


def _heartbeat_loop():
    recv_time = 0

    while True:
        while time() < recv_time + poll_duration:
            gevent.sleep(poll_interval)

        if _wakeup_recv_file.read(1):
            recv_time = time()


class Session(BaseSession):
    """A version of ninchat.client.Session which executes callbacks
    in the main thread's gevent event loop."""

    _new_session = lib.new_gevent_session

    def __init__(self):
        global _heartbeat_init
        if not _heartbeat_init:
            gevent.spawn(_heartbeat_loop)
            _heartbeat_init = True

        super(Session, self).__init__()

    def _call(self, *sig):
        _pending_calls.append(sig)


@ffi.def_extern()
def gevent_wakeup():
    global _wakeup_send_time
    now = time()
    if now - _wakeup_send_time > poll_duration:
        if os.write(_wakeup_send_fd, b"\0"):
            _wakeup_send_time = now


@ffi.def_extern()
def gevent_invoke():
    done = 0
    try:
        for sig in _pending_calls:
            done += 1
            call = sig[0]
            args = sig[1:]
            try:
                call(*args)
            except Exception:
                log.exception("raised by callback")
    finally:
        del _pending_calls[:done]


del gevent_wakeup
del gevent_invoke
