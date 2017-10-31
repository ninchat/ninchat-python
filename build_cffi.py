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

from __future__ import absolute_import, print_function

from os import environ
from os.path import dirname, exists
from subprocess import check_call

from cffi import FFI

gocommand = environ.get("GO", "go")
gobuildmode = environ.get("GOBUILDMODE", "c-archive")
gobuildout = environ.get("GOBUILDOUT", "build/libninchat.a")

if not exists(gobuildout):
    print("building", gobuildout, "with", gocommand)
    check_call([gocommand, "build", "-buildmode={}".format(gobuildmode), "-o", gobuildout, "go/src/github.com/ninchat/ninchat-go/c/library.go"])

ffibuilder = FFI()

python_callbacks = r"""
DECL void callback_session_event(
		void *ctx,
		const char *params,
		size_t params_len);

DECL void callback_event(
		void *ctx,
		const char *params,
		size_t params_len,
		const ninchat_frame payload[],
		unsigned int payload_len,
		bool last_reply);

DECL void callback_close(void *ctx);

DECL void callback_conn_state(void *ctx, const char *state);

DECL void callback_conn_active(void *ctx);

DECL void callback_log(void *ctx, const char *msg, size_t msg_len);

DECL void gevent_wakeup(void);

DECL void gevent_invoke(void);
"""

cdef = r"""
void free(void *);

ninchat_session new_common_session(void *ctx);

ninchat_session new_gevent_session(void *ctx);

void set_payload_frame(
		ninchat_frame payload[],
		unsigned int i,
		const void *frame_data,
		size_t frame_size);

const ninchat_frame *payload_frame(const ninchat_frame vec[], unsigned int i);

const char *frame_data(const ninchat_frame *frame);

size_t frame_size(const ninchat_frame *frame);

""" + python_callbacks.replace("DECL", 'extern "Python"')

with open("go/src/github.com/ninchat/ninchat-go/include/ninchat.h") as f:
    header = ""
    for line in f:
        if "CFFI BEGIN" in line:
            header = ""
        elif "CFFI END" in line:
            ffibuilder.cdef(header + cdef)
        elif not line.startswith("#"):
            header += line

source = r"""
#include <stddef.h>
#include <string.h>

#include <pthread.h>

#include <ninchat.h>

""" + python_callbacks.replace("DECL", "static") + r"""

#define COMMON_CALLBACK_PROLOGUE \
	PyGILState_STATE gstate = PyGILState_Ensure(); \
	Py_BEGIN_ALLOW_THREADS

#define COMMON_CALLBACK_EPILOGUE \
	Py_END_ALLOW_THREADS \
	PyGILState_Release(gstate);

static void common_callback_session_event(
		void *ctx,
		const char *params,
		size_t params_len)
{
	COMMON_CALLBACK_PROLOGUE
	callback_session_event(ctx, params, params_len);
	COMMON_CALLBACK_EPILOGUE
}

static void common_callback_event(
		void *ctx,
		const char *params,
		size_t params_len,
		const ninchat_frame payload[],
		unsigned int payload_len,
		bool last_reply)
{
	COMMON_CALLBACK_PROLOGUE
	callback_event(ctx, params, params_len, payload, payload_len, last_reply);
	COMMON_CALLBACK_EPILOGUE
}

static void common_callback_close(void *ctx)
{
	COMMON_CALLBACK_PROLOGUE
	callback_close(ctx);
	COMMON_CALLBACK_EPILOGUE
}

static void common_callback_conn_state(void *ctx, const char *state)
{
	COMMON_CALLBACK_PROLOGUE
	callback_conn_state(ctx, state);
	COMMON_CALLBACK_EPILOGUE
}

static void common_callback_conn_active(void *ctx)
{
	COMMON_CALLBACK_PROLOGUE
	callback_conn_active(ctx);
	COMMON_CALLBACK_EPILOGUE
}

static void common_callback_log(void *ctx, const char *msg, size_t msg_len)
{
	COMMON_CALLBACK_PROLOGUE
	callback_log(ctx, msg, msg_len);
	COMMON_CALLBACK_EPILOGUE
}

static ninchat_session new_common_session(void *ctx)
{
	ninchat_session s = ninchat_session_new();
	ninchat_session_on_session_event(s, common_callback_session_event, ctx);
	ninchat_session_on_event(s, common_callback_event, ctx);
	ninchat_session_on_close(s, common_callback_close, ctx);
	ninchat_session_on_conn_state(s, common_callback_conn_state, ctx);
	ninchat_session_on_conn_active(s, common_callback_conn_active, ctx);
	ninchat_session_on_log(s, common_callback_log, ctx);
	return s;
}

static pthread_mutex_t gevent_lock = PTHREAD_MUTEX_INITIALIZER;

static int gevent_invoke_py(void *dummy)
{
	(void) dummy;

	Py_BEGIN_ALLOW_THREADS
	pthread_mutex_lock(&gevent_lock);

	gevent_invoke();

	pthread_mutex_unlock(&gevent_lock);
	Py_END_ALLOW_THREADS

	return 0;
}

#define GEVENT_CALLBACK_PROLOGUE \
	COMMON_CALLBACK_PROLOGUE \
	pthread_mutex_lock(&gevent_lock);

#define GEVENT_CALLBACK_EPILOGUE \
	pthread_mutex_unlock(&gevent_lock); \
	if (Py_AddPendingCall(gevent_invoke_py, NULL) == 0) \
		gevent_wakeup(); \
	COMMON_CALLBACK_EPILOGUE

static void gevent_callback_session_event(
		void *ctx,
		const char *params,
		size_t params_len)
{
	GEVENT_CALLBACK_PROLOGUE
	callback_session_event(ctx, params, params_len);
	GEVENT_CALLBACK_EPILOGUE
}

static void gevent_callback_event(
		void *ctx,
		const char *params,
		size_t params_len,
		const ninchat_frame payload[],
		unsigned int payload_len,
		bool last_reply)
{
	GEVENT_CALLBACK_PROLOGUE
	callback_event(ctx, params, params_len, payload, payload_len, last_reply);
	GEVENT_CALLBACK_EPILOGUE
}

static void gevent_callback_close(void *ctx)
{
	GEVENT_CALLBACK_PROLOGUE
	callback_close(ctx);
	GEVENT_CALLBACK_EPILOGUE
}

static void gevent_callback_conn_state(void *ctx, const char *state)
{
	GEVENT_CALLBACK_PROLOGUE
	callback_conn_state(ctx, state);
	GEVENT_CALLBACK_EPILOGUE
}

static void gevent_callback_conn_active(void *ctx)
{
	GEVENT_CALLBACK_PROLOGUE
	callback_conn_active(ctx);
	GEVENT_CALLBACK_EPILOGUE
}

static void gevent_callback_log(void *ctx, const char *msg, size_t msg_len)
{
	GEVENT_CALLBACK_PROLOGUE
	callback_log(ctx, msg, msg_len);
	GEVENT_CALLBACK_EPILOGUE
}

static ninchat_session new_gevent_session(void *ctx)
{
	ninchat_session s = ninchat_session_new();
	ninchat_session_on_session_event(s, gevent_callback_session_event, ctx);
	ninchat_session_on_event(s, gevent_callback_event, ctx);
	ninchat_session_on_close(s, gevent_callback_close, ctx);
	ninchat_session_on_conn_state(s, gevent_callback_conn_state, ctx);
	ninchat_session_on_conn_active(s, gevent_callback_conn_active, ctx);
	ninchat_session_on_log(s, gevent_callback_log, ctx);
	return s;
}

static void set_payload_frame(
		ninchat_frame payload[],
		unsigned int i,
		const void *data,
		size_t size)
{
	memset(&payload[i], 0, sizeof (ninchat_frame));
	payload[i].data = data;
	payload[i].size = size;
}

static const ninchat_frame *payload_frame(
		const ninchat_frame payload[],
		unsigned int i)
{
	return &payload[i];
}

static const char *frame_data(const ninchat_frame *frame)
{
	return frame->data;
}

static size_t frame_size(const ninchat_frame *frame)
{
	return frame->size;
}
"""

ffibuilder.set_source("_ninchat_cffi", source, include_dirs=["go/src/github.com/ninchat/ninchat-go/include"], library_dirs=[dirname(gobuildout)], libraries=["ninchat"])

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
