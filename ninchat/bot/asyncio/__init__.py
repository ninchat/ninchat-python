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

import asyncio
import json
import logging
from functools import partial
from pprint import pformat
from random import random

from ninchat.client.asyncio import Session

log = logging.getLogger("ninchat.bot")
loop = asyncio.get_event_loop()
event_handlers = {}
message_handlers = {}


def register_event(f):
    event_handlers[f.__name__] = lambda ctx, params, payload: f(ctx, params)
    return f


def register_payload_event(f):
    event_handlers[f.__name__] = f
    return f


def register_message_received_event(f):
    message_handlers["ninchat.com/" + f.__name__.replace("_", "/")] = f
    return f


class Context:

    def __init__(self, handler, session, user_id):
        self.handler = handler
        self.session = session
        self.user_id = user_id
        self.dialogues = {}


class Dialogue:

    def __init__(self, user_id):
        self.user_id = user_id
        self.backlog = []
        self.loading = False
        self.writing = 0
        self.closed = False
        self.latest_send_time = loop.time()

    def begin(self, ctx):
        text = ctx.handler.on_begin(self.user_id)
        if text is not None:
            send_message(ctx, self.user_id, text)

    def load(self, ctx):
        log.info("user %s: loading messages", self.user_id)
        self.loading = True
        loop.create_task(self._load_messages(ctx))

    def reload(self, ctx):
        # TODO
        log.error("user %s: reloading messages not implemented", self.user_id)

    def received(self, ctx, params, payload):
        if not self.closed:
            if "action_id" not in params:  # Unsolicited message from peer
                self._buffer_message(params, payload)
                if self.loading:
                    log.info("user %s: buffering message", self.user_id)
                else:
                    log.info("user %s: processing message", self.user_id)
                    self._process_backlog(ctx)

        return not self.closed or self.loading

    def user_deleted(self, ctx):
        log.info("user %s: user deleted; hiding dialogue", self.user_id)

        update_dialogue(ctx, self.user_id, dialogue_status="hidden", member_attrs=dict(writing=False))

        return self._close(ctx)

    def hidden(self, ctx):
        log.info("user %s: dialogue hidden", self.user_id)

        return self._close(ctx)

    def _close(self, ctx):
        ctx.handler.on_close(self.user_id)

        self.closed = True
        return self.loading

    def _buffer_message(self, params, payload):
        key = params["message_id"]
        text = json.loads(payload[0].decode())["text"]
        self.backlog.append((key, text))

    async def _load_messages(self, ctx):
        try:
            replies = []
            params, _ = await load_history(ctx, self.user_id, lambda *args: replies.append(args))

            if params["event"] != "error":
                messages = []

                for params, payload, last_reply in replies:
                    if params["event"] == "message_received" and params["message_type"] == "ninchat.com/text":
                        if params["message_user_id"] == ctx.user_id:
                            messages = []
                        else:
                            messages.append((params, payload))

                for params, payload in messages:
                    self._buffer_message(params, payload)
        finally:
            self.loading = False
            if self.closed:
                del ctx.dialogues[self.user_id]

        log.info("user %s: processing buffered messages", self.user_id)
        self._process_backlog(ctx)

    def _process_backlog(self, ctx):
        if self.backlog:
            now = loop.time()

            self.backlog.sort()
            inputs = [t for k, t in self.backlog]
            self.backlog = []

            text = ctx.handler.on_messages(self.user_id, inputs)
            if text:
                t1 = now + 1 + random()
                t2 = now + 2 * random() + len(text) / 10

                if t2 < self.latest_send_time:
                    t2 = self.latest_send_time + random()

                loop.call_at(t1, self._start_replying, ctx, t2, text)
                self.latest_send_time = t2

    def _start_replying(self, ctx, t, text):
        if not self.writing:
            update_dialogue(ctx, self.user_id, member_attrs=dict(writing=True))
        self.writing += 1

        loop.call_at(t, self._finish_reply, ctx, text)

    def _finish_reply(self, ctx, text):
        self.writing -= 1
        if not self.writing:
            update_dialogue(ctx, self.user_id, member_attrs=dict(writing=False))

        send_message(ctx, self.user_id, text)


def update_dialogue(ctx, user_id, **params):
    params.update({
        "action":  "update_dialogue",
        "user_id": user_id,
    })
    ctx.session.send(params)


def send_message(ctx, user_id, text):
    ctx.session.send({
        "action":       "send_message",
        "user_id":      user_id,
        "message_type": "ninchat.com/text",
    }, [json.dumps({"text": text}).encode()])


def load_history(ctx, user_id, on_reply):
    return ctx.session.call({
        "action":         "load_history",
        "user_id":        user_id,
        "message_id":     "",
        "history_length": 1000,
        "history_order":  1,
    }, on_reply=on_reply)


def accept_audience(ctx, queue_id, queue_attrs):
    if queue_attrs.get("length"):
        ctx.session.send({
            "action":   "accept_audience",
            "queue_id": queue_id,
        })


@register_event
def error(ctx, params):
    log.error("error: %s", params)


@register_event
def session_created(ctx, params):
    dialogues = {}

    for user_id, info in params.get("user_dialogues", {}).items():
        try:
            d = ctx.dialogues.pop(user_id)
        except KeyError:
            d = None

        members = info.get("dialogue_members", {})

        if "queue_id" in members.get(user_id, {}) and not members.get(ctx.user_id, {}).get("audience_ended"):
            if d:
                d.reload(ctx)
            else:
                d = Dialogue(user_id)
                d.load(ctx)

            dialogues[user_id] = d

    for user_id, d in ctx.dialogues:
        alive = d.hidden(ctx)
        if alive:
            dialogues[user_id] = d

    ctx.dialogues = dialogues

    for queue_id, info in params.get("user_queues", {}).items():
        accept_audience(ctx, queue_id, info["queue_attrs"])


@register_event
def queue_found(ctx, params):
    accept_audience(ctx, params["queue_id"], params["queue_attrs"])


@register_event
def queue_updated(ctx, params):
    accept_audience(ctx, params["queue_id"], params["queue_attrs"])


@register_event
def dialogue_updated(ctx, params):
    user_id = params["user_id"]
    status = params["dialogue_status"]

    try:
        d = ctx.dialogues[user_id]
    except KeyError:
        if status != "hidden":
            d = ctx.dialogues[user_id] = Dialogue(user_id)
            d.begin(ctx)
    else:
        if status == "hidden":
            alive = d.hidden(ctx)
            if not alive:
                del ctx.dialogues[user_id]


@register_payload_event
def message_received(ctx, params, payload):
    if log.isEnabledFor(logging.DEBUG):
        log.debug("payload[0]:\n%s", pformat(json.loads(payload[0].decode())))

    f = message_handlers.get(params["message_type"])
    if f:
        f(ctx, params, payload)


@register_message_received_event
def info_user(ctx, params, payload):
    user_id = params["user_id"]
    if json.loads(payload[0].decode()).get("user_deleted"):
        d = ctx.dialogues.get(user_id)
        if d:
            alive = d.user_deleted(ctx)
            if not alive:
                del ctx.dialogues[user_id]


@register_message_received_event
def text(ctx, params, payload):
    user_id = params.get("user_id")
    if user_id:
        d = ctx.dialogues.get(user_id)
        if d:
            alive = d.received(ctx, params, payload)
            if not alive:
                del ctx.dialogues[user_id]


async def run(handler_factory, *, identity):
    events = asyncio.Queue()

    def on_session_event(params):
        if params["event"] == "error":
            log.error("session: %s", params)
            params = None
        loop.create_task(events.put((params, None)))

    def on_event(params, payload, last_reply):
        loop.create_task(events.put((params, payload)))

    params = {
        "message_types": list(message_handlers.keys()),
    }

    if identity:
        params["identity_type"], params["identity_name"], params["identity_auth"] = identity

    session = Session()
    session.set_params(params)
    session.on_session_event = on_session_event
    session.on_event = on_event

    outgoing_messages = asyncio.Queue()
    handler = handler_factory(outgoing_messages)

    async def process_outgoing_messages(ctx):
        while True:
            msg = await outgoing_messages.get()
            if msg is None:
                break

            user_id, text = msg
            send_message(ctx, user_id, text)

    try:
        async with session as params:
            ctx = Context(handler, session, params["user_id"])
            loop.create_task(process_outgoing_messages(ctx))

            while True:
                params, payload = await events.get()
                if params is None:
                    break

                name = params["event"]

                if log.isEnabledFor(logging.DEBUG):
                    log.debug("event: %s\n%s", name, pformat(params))
                else:
                    log.info("event: %s", name)

                f = event_handlers.get(name)
                if f:
                    f(ctx, params, payload)
    finally:
        outgoing_messages.put(None)
