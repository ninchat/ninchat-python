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

from __future__ import absolute_import

__all__ = ["APIError"]

import json

import ninchat

url = "https://api.ninchat.com/v2/call"

request_headers = {
    "Accept":       "application/json",
    "Content-Type": "application/json",
}


class APIError(ninchat.APIError):
    """Raised by check_call and checked call function calls.

    .. attribute:: event

       Dict[str, Any]
    """


def request_content(params, **kwargs):
    # type: (params: Dict[str, Any], *, identity: Optional[Sequence[str, str, str]]=None) -> bytes
    params = params.copy()

    identity = kwargs.get("identity")
    if identity:
        params["caller_type"], params["caller_name"], params["caller_auth"] = identity

    return json.dumps(params, separators=(",", ":")).encode()


def check_event(e):
    # type: (e: Dict[str, Any]) -> None
    if e["event"] == "error":
        raise APIError(e)
