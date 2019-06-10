# Copyright (c) 2013, Somia Reality Oy
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

from __future__ import absolute_import, print_function

import time

from ninchat import master


def test_master():
    key = (
        "22nlihvg",
        "C58sAn+Dp2Ogb2+FdfSNg3J0ImMYfYodUUgXFF2OPo0=",
    )
    expire = time.time() + 60
    puppet_attrs = [
        ("name", "Enforced"),
    ]
    user_id = "22ouqqbp"
    channel_id = "1bfbr0u"
    member_attrs = [
        ("silenced", False),
    ]
    metadata = dict(
        foo=3.14159,
        bar="asdf",
        baz=[1, 2, 3],
        quux={
            "a": 100,
            "b": 200,
        },
    )

    dump(master.sign_create_session(key, expire))
    dump(master.sign_create_session(key, expire, puppet_attrs))
    dump(master.sign_create_session_for_user(key, expire, user_id))
    dump(master.sign_join_channel(key, expire, channel_id))
    dump(master.sign_join_channel(key, expire, channel_id, member_attrs))
    dump(master.sign_join_channel_for_user(key, expire, channel_id, user_id))
    dump(master.sign_join_channel_for_user(key, expire, channel_id, user_id, member_attrs))

    dump(master.secure_metadata(key, expire, metadata))
    dump(master.secure_metadata_for_user(key, expire, metadata, user_id))


def dump(s):
    print()
    print("Size:", len(s))
    print("Data:", s)
