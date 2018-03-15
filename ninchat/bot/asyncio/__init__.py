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
from pprint import pformat
from random import random

from ninchat.client.asyncio import Session

log = logging.getLogger("ninchat.bot")
verbose_logging = False
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

    def __init__(self, handler, session, user_id, debug):
        self.handler = handler
        self.session = session
        self.user_id = user_id
        self.debug = debug
        self.dialogues = {}


class Dialogue:

    def __init__(self, user_id):
        self.user_id = user_id
        self.backlog = []
        self.loading = False
        self.peer_writing = False
        self.self_writing = 0
        self.closed = False
        self.latest_send_time = loop.time()

    def begin(self, ctx):
        msgs = ctx.handler.on_begin(self.user_id)
        if msgs:
            self.send_messages(ctx, msgs)

    def set_peer_writing(self, ctx, writing):
        if self.peer_writing != writing:
            self.peer_writing = writing
            ctx.handler.on_writing(self.user_id, writing)

    def load(self, ctx):
        log.debug("user %s: loading messages", self.user_id)
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
                    log.debug("user %s: buffering message", self.user_id)
                else:
                    log.debug("user %s: processing message", self.user_id)
                    self._process_backlog(ctx)

        return not self.closed or self.loading

    def user_deleted(self, ctx):
        log.debug("user %s: user deleted; hiding dialogue", self.user_id)

        update_dialogue(ctx, self.user_id, dialogue_status="hidden", member_attrs=dict(writing=False))

    def hidden(self, ctx):
        log.debug("user %s: dialogue hidden", self.user_id)

        if self.peer_writing:
            self.peer_writing = False
            ctx.handler.on_writing(self.user_id, False)

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

        log.debug("user %s: processing buffered messages", self.user_id)
        self._process_backlog(ctx)

    def _process_backlog(self, ctx):
        if self.backlog:
            self.backlog.sort()
            inputs = [t for k, t in self.backlog]
            self.backlog = []

            msgs = ctx.handler.on_messages(self.user_id, inputs)
            if msgs:
                self.send_messages(ctx, msgs, 1 + random())

    def send_messages(self, ctx, msgs, delay=0):
        t1 = loop.time()
        t2 = t1 + random() + len(msgs[0]["text"]) * 0.1

        if delay:
            t1 += delay
            t2 += delay

        if t2 < self.latest_send_time:
            t2 = self.latest_send_time + random()

        loop.call_at(t1, self._start_replying, ctx, t2, msgs)
        self.latest_send_time = t2

    def _start_replying(self, ctx, t, msgs):
        if not self.self_writing:
            update_dialogue(ctx, self.user_id, member_attrs=dict(writing=True))
        self.self_writing += 1

        loop.call_at(t, self._finish_reply, ctx, msgs)

    def _finish_reply(self, ctx, msgs):
        self.self_writing -= 1
        if not self.self_writing:
            update_dialogue(ctx, self.user_id, member_attrs=dict(writing=False))

        for msg in msgs:
            send_message(ctx, self.user_id, msg)


def update_dialogue(ctx, user_id, **params):
    params.update({
        "action":  "update_dialogue",
        "user_id": user_id,
    })
    ctx.session.send(params)


def send_message(ctx, user_id, msg):
    try:
        debug_info = msg.pop("debug")
    except KeyError:
        debug_info = None

    def send_debug(params, payload, last_reply):
        if ctx.debug and debug_info and "message_id" in params:
            debug_msg = {
                "debug":      debug_info,
                "message_id": params["message_id"],
            }

            ctx.session.send({
                "action":       "send_message",
                "user_id":      user_id,
                "message_type": "ninch.at/bot/debug",
            }, [json.dumps(debug_msg).encode()])

    ctx.session.send({
        "action":       "send_message",
        "user_id":      user_id,
        "message_type": "ninchat.com/text",
    }, [json.dumps(msg).encode()], send_debug if debug_info else None)


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
        self_attrs = members.get(ctx.user_id, {})
        peer_attrs = members.get(user_id, {})

        if "queue_id" in peer_attrs and not self_attrs.get("audience_ended"):
            if d:
                d.reload(ctx)
            else:
                d = Dialogue(user_id)
                d.load(ctx)

            d.set_peer_writing(ctx, peer_attrs.get("writing", False))
            dialogues[user_id] = d

    for user_id, d in ctx.dialogues.items():
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
    writing = params["dialogue_members"][user_id].get("writing", False)

    try:
        d = ctx.dialogues[user_id]
    except KeyError:
        if status != "hidden":
            d = ctx.dialogues[user_id] = Dialogue(user_id)
            d.begin(ctx)
            d.set_peer_writing(ctx, writing)
    else:
        if status == "hidden":
            alive = d.hidden(ctx)
            if not alive:
                del ctx.dialogues[user_id]
        else:
            d.set_peer_writing(ctx, writing)


@register_payload_event
def message_received(ctx, params, payload):
    if verbose_logging:
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
            d.user_deleted(ctx)


@register_message_received_event
def text(ctx, params, payload):
    user_id = params.get("user_id")
    if user_id:
        d = ctx.dialogues.get(user_id)
        if d:
            alive = d.received(ctx, params, payload)
            if not alive:
                del ctx.dialogues[user_id]


async def run(handler_factory, *, identity, debug_messages=False):
    events = asyncio.Queue()

    def on_session_event(params):
        if params["event"] == "error":
            log.error("session: %s", params)
            params = None
        loop.create_task(events.put((params, None)))

    def on_event(params, payload, last_reply):
        loop.create_task(events.put((params, payload)))

    message_types = list(message_handlers.keys())
    if debug_messages:
        message_types.append("ninch.at/bot/debug")

    params = {
        "message_types": message_types,
    }

    if identity:
        params["identity_type"] = identity["type"]
        params["identity_name"] = identity["name"]
        params["identity_auth"] = identity["auth"]

    session = Session()
    session.set_params(params)
    session.on_session_event = on_session_event
    session.on_event = on_event

    outgoing_messages = asyncio.Queue()
    handler = handler_factory(outgoing_messages, debug_messages)

    async def process_outgoing_messages(ctx):
        while True:
            item = await outgoing_messages.get()
            if item is None:
                break

            user_id, msg = item
            d = ctx.dialogues.get(user_id)
            if d:
                d.send_messages(ctx, [msg])

    try:
        async with session as params:
            ctx = Context(handler, session, params["user_id"], debug_messages)
            loop.create_task(process_outgoing_messages(ctx))

            while True:
                params, payload = await events.get()
                if params is None:
                    break

                name = params["event"]

                if verbose_logging:
                    log.debug("event: %s\n%s", name, pformat(params))
                else:
                    log.debug("event: %s", name)

                f = event_handlers.get(name)
                if f:
                    f(ctx, params, payload)
    finally:
        outgoing_messages.put(None)
