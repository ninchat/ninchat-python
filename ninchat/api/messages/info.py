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

from . import Message, declare_messagetype


@declare_messagetype("ninchat.com/info/user")
class UserInfoMessage(Message):
    """Stub for the ninchat.com/info/user message type.
    """
    __slots__ = Message.__slots__


@declare_messagetype("ninchat.com/info/channel")
class ChannelInfoMessage(Message):
    """Stub for the ninchat.com/info/channel message type.
    """
    __slots__ = Message.__slots__


@declare_messagetype("ninchat.com/info/join")
class JoinInfoMessage(Message):
    """Stub for the ninchat.com/info/join message type.
    """
    __slots__ = Message.__slots__


@declare_messagetype("ninchat.com/info/part")
class PartInfoMessage(Message):
    """Stub for the ninchat.com/info/part message type.
    """
    __slots__ = Message.__slots__


@declare_messagetype("ninchat.com/info/member")
class MemberInfoMessage(Message):
    """Stub for the ninchat.com/info/member message type.
    """
    __slots__ = Message.__slots__


@declare_messagetype("ninchat.com/info/access")
class AccessInfoMessage(Message):
    """Stub for the ninchat.com/info/access message type.
    """
    __slots__ = Message.__slots__
