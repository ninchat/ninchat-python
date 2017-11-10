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

"""Utilities for using master keys.

The master key id and secret may be obtained with the `create_master_key
<https://ninchat.com/api#create_master_key>`_ API action.  The *key* argument
taken by all functions is a pair (e.g. a tuple) consisting of the id and the
secret.

The signatures and secured metadata may be used once before the expiration
time.  Expiration time is specified in Unix time (seconds since 1970-01-01
UTC), and may not be more than one week in the future.


Signature generation
--------------------

The following functions create values for the master_sign parameter of some API
actions.  The *member_attrs* argument is expected to be an iterable with pair
(e.g. tuple) elements, as opposed to the API actions which expect it as a dict.

For use with the `create_session <https://ninchat.com/api#create_session>`_
action:

.. autofunction:: sign_create_session
.. autofunction:: sign_create_session_for_user

For use with the `join_channel <https://ninchat.com/api#join_channel>`_ action:

.. autofunction:: sign_join_channel
.. autofunction:: sign_join_channel_for_user


Metadata encryption
-------------------

The following functions create values for the "secure" property of the
audience_metadata parameter of the `request_audience
<https://ninchat.com/api#request_audience>`_ API action.  The *metadata*
argument should be a dict or None.

(The functions are unavailable if cryptography or PyCrypto can't be found.)

.. autofunction:: secure_metadata
.. autofunction:: secure_metadata_for_user

"""

from __future__ import absolute_import

from .sign import (
    sign_create_session,
    sign_create_session_for_user,
    sign_join_channel,
    sign_join_channel_for_user,
)

# avoid warnings
sign_create_session
sign_create_session_for_user
sign_join_channel
sign_join_channel_for_user

try:
    from .secure import (
        secure_metadata,
        secure_metadata_for_user,
    )

    # avoid warnings
    secure_metadata
    secure_metadata_for_user
except ImportError:
    pass
