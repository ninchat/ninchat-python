# Copyright (c) 2018, Somia Reality Oy
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

from . import _AbstractObjectMessage, declare_messagetype
from .. import is_bool


@declare_messagetype("ninchat.com/rtc/answer")
class AnswerRTCMessage(_AbstractObjectMessage):
    _specs = {
        "sdp": (bool, True),
    }


@declare_messagetype("ninchat.com/rtc/call")
class CallRTCMessage(_AbstractObjectMessage):
    _specs = {}  # type: dict


@declare_messagetype("ninchat.com/rtc/ice-candidate")
class IceCandidateRTCMessage(_AbstractObjectMessage):
    _specs = {
        "candidate": (bool, True),
    }


@declare_messagetype("ninchat.com/rtc/hang-up")
class HangUpRTCMessage(_AbstractObjectMessage):
    _specs = {}  # type: dict


@declare_messagetype("ninchat.com/rtc/offer")
class OfferRTCMessage(_AbstractObjectMessage):
    _specs = {
        "sdp": (bool, True),
    }


@declare_messagetype("ninchat.com/rtc/pick-up")
class PickUpRTCMessage(_AbstractObjectMessage):
    _specs = {
        "answer": (is_bool, True),
        "busy": (is_bool, False),
        "unsupported": (is_bool, False),
    }
