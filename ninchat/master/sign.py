# Copyright (c) 2013-2014, Somia Reality Oy
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

import base64
import hashlib
import hmac
import json
import random
import struct

def sign_create_session(key, expire):
	"""Use when creating a new user.  The user will become a puppet of the master.
	"""
	msg = [
		("action", "create_session"),
	]

	return _sign(key, expire, msg)

def sign_create_session_for_user(key, expire, user_id):
	"""Use when authenticating an existing user.  The user must be a puppet of the
	   master.  The *user_id* specified here must be repeated in the API call.
	"""
	msg = [
		("action", "create_session"),
		("user_id", user_id),
	]

	return _sign(key, expire, msg)

def sign_join_channel(key, expire, channel_id, member_attrs=None):
	"""For use by any user.  The master must own the channel.  The *channel_id* and
	   *member_attrs* specified here must be repeated in the API call.
	"""
	return _sign_join_channel(key, expire, channel_id, member_attrs, [])

def sign_join_channel_for_user(key, expire, channel_id, user_id, member_attrs=None):
	"""For use by the specified user only.  The master must own the channel.  The
	   *channel_id* and *member_attrs* specified here must be repeated in the
	   API call.
	"""
	msg = [
		("user_id", user_id),
	]

	return _sign_join_channel(key, expire, channel_id, member_attrs, msg) + "-1"

def _sign_join_channel(key, expire, channel_id, member_attrs, msg):
	msg.append(("action", "join_channel"))
	msg.append(("channel_id", channel_id))

	if member_attrs:
		member_attrs = sorted(member_attrs)
		if member_attrs:
			msg.append(("member_attrs", member_attrs))

	return _sign(key, expire, msg)

def _sign(key, expire, msg):
	key_id, key_secret = key
	expire = int(expire)
	nonce = base64.b64encode(struct.pack(b"Q", random.randint(0, (1 << 48) - 1))[:6]).decode("ascii")

	msg.append(("expire", expire))
	msg.append(("nonce", nonce))
	msg.sort()

	msg_json = json.dumps(msg, separators=(",", ":")).encode("utf-8")

	digest = hmac.new(base64.b64decode(key_secret), msg_json, hashlib.sha512).digest()
	digest_base64 = base64.b64encode(digest)

	return "{}-{}-{}-{}".format(key_id, expire, nonce, digest_base64)
