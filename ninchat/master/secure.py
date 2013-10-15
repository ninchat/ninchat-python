# Copyright (c) 2014, Somia Reality Oy
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
import json

import Crypto.Cipher.AES
import Crypto.Random

def secure_metadata(key, expire, metadata):
	"""For use with any user.
	"""
	return _secure_metadata(key, expire, metadata, {})

def secure_metadata_for_user(key, expire, metadata, user_id):
	"""For use with the specified user only.
	"""
	msg = {
		"user_id": user_id,
	}

	return _secure_metadata(key, expire, metadata, msg)

def _secure_metadata(key, expire, metadata, msg):
	key_id, key_secret = key

	msg["expire"] = expire
	msg["metadata"] = metadata

	msg_json = json.dumps(msg, separators=(",", ":")).encode("utf-8")

	hasher = hashlib.sha512()
	hasher.update(msg_json)
	digest = hasher.digest()
	msg_hashed = digest + msg_json

	block_mask = Crypto.Cipher.AES.block_size - 1
	padded_size = (len(msg_hashed) + block_mask) & ~block_mask
	msg_padded = msg_hashed.ljust(padded_size, b"\0")

	iv = Crypto.Random.new().read(Crypto.Cipher.AES.block_size)

	cipher = Crypto.Cipher.AES.new(base64.b64decode(key_secret), Crypto.Cipher.AES.MODE_CBC, iv)
	msg_encrypted = cipher.encrypt(msg_padded)

	msg_iv = iv + msg_encrypted
	msg_base64 = base64.b64encode(msg_iv)

	return "{}-{}".format(key_id, msg_base64)
