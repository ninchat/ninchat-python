# Copyright (c) 2012-2013, Somia Reality Oy
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

import json

from ninchat import api

class ParameterError(Exception):
	"""API action is missing a required parameter or the parameter value is
	invalid.  The corresponding ninchat.api.Parameter instance may be read from
	the param attribute (if one exists).
	"""
	def __init__(self, message, param=None):
		super(ParameterError, self).__init__(message)
		self.param = param

class Action(object):

	def __init__(self, action, event_id=None, payload=None, **params):
		self._params = params
		self.payload = payload or []

		specs = api.actions[action].params

		for name, spec in specs.items():
			value = self._params.get(name)
			if value is None:
				if spec.required:
					raise ParameterError(
							"%r is missing from %r action" % (name, action),
							spec)
			else:
				if not spec.validate(value):
					raise ParameterError(
							"%r value is invalid in %r action: %r" %
							(name, action, value),
							spec)

		for name in self._params:
			if name not in specs:
				raise ParameterError(
						"unknown %r in %r action" % (name, action))

		self._params["action"] = action

		if event_id is not None:
			self._params["event_id"] = event_id

		if self.payload:
			self._params["frames"] = len(self.payload)

	def __str__(self):
		return self._params["action"]

	def __repr__(self):
		return "<Action %r %s%s>" % (
			self._params["action"],
			" ".join(
					"%s %r" % (k, v) for k, v in sorted(self._params.items())
					if k not in ("action", "frames")),
			(" payload " + " ".join(
					"%r" % p for p in self.payload)) if self.payload else "")

	@property
	def frames(self):
		return [json.dumps(self._params, separators=(",", ":"))] + self.payload

class SessionAction(Action):

	def __init__(self, action, session_id=None, event_id=None):
		self._params = { "action": action }
		self.payload = []

		if session_id is not None:
			self._params["session_id"] = session_id

		if event_id is not None:
			self._params["event_id"] = event_id