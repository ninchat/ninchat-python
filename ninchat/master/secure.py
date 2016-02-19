# Copyright (c) 2014-2016, Somia Reality Oy
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
import os

_AES256_BLOCK_SIZE = 16
_AES256_BLOCK_MASK = _AES256_BLOCK_SIZE - 1
_AES256CBC_IV_SIZE = _AES256_BLOCK_SIZE

try:
	from cryptography.hazmat.backends import default_backend as _default_backend
	from cryptography.hazmat.primitives.ciphers import Cipher as _Cipher
	from cryptography.hazmat.primitives.ciphers.algorithms import AES as _AES
	from cryptography.hazmat.primitives.ciphers.modes import CBC as _CBC
except ImportError:
	from Crypto.Cipher import AES as _AES

	# PyCrypto
	def _aes256cbc_encrypt(key, iv, plaintext):
		cipher = _AES.new(key, _AES.MODE_CBC, iv)
		ciphertext = cipher.encrypt(plaintext)
		return ciphertext
else:
	# cryptography
	def _aes256cbc_encrypt(key, iv, plaintext):
		algo = _AES(key)
		mode = _CBC(iv)
		backend = _default_backend()
		cipher = _Cipher(algo, mode, backend)
		encryptor = cipher.encryptor()
		ciphertext = encryptor.update(plaintext)
		ciphertext += encryptor.finalize()
		return ciphertext

def secure_metadata(key, expire, metadata):
	"""For use by any user.
	"""
	return _secure_metadata(key, expire, metadata, {})

def secure_metadata_for_user(key, expire, metadata, user_id):
	"""For use by the specified user only.
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

	padded_size = (len(msg_hashed) + _AES256_BLOCK_MASK) & ~_AES256_BLOCK_MASK
	msg_padded = msg_hashed.ljust(padded_size, b"\0")

	iv = os.urandom(_AES256CBC_IV_SIZE)
	msg_encrypted = _aes256cbc_encrypt(base64.b64decode(key_secret.encode()), iv, msg_padded)
	msg_iv = iv + msg_encrypted

	msg_base64 = base64.b64encode(msg_iv)

	return "%s-%s" % (key_id, msg_base64)
