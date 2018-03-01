import argparse
import asyncio
import json
from collections import defaultdict
from os import environ

from . import run
from . import utils

loop = asyncio.get_event_loop()


class Handler:

    def __init__(self, queue, debug=False):
        self.queue = queue
        self.debug = debug
        self.nums = defaultdict(int)

    def on_begin(self, user_id):
        self.nums[user_id] = 0
        msg = {
            "text": "Hello! " + str(self.nums[user_id]),
        }
        self.include_debug(msg)
        return msg

    def on_writing(self, user_id, writing):
        pass

    def on_messages(self, user_id, messages):
        self.nums[user_id] += 1
        msg = {
            "text": 'Really, "' + "\n".join(messages) + '"? ' + str(self.nums[user_id]),
        }
        self.include_debug(msg)
        return msg

    def on_close(self, user_id):
        try:
            del self.nums[user_id]
        except KeyError:
            pass

    def include_debug(self, msg):
        if self.debug:
            msg["debug"] = {
                "enabled": True,
            }


def main(handler_factory=Handler, *, identity_file=None):
    args = None
    params = {}

    parser = argparse.ArgumentParser()
    parser.add_argument("--identity-file", metavar="PATH", default=identity_file, help='JSON document containing "type", "name" and "auth" properties')
    parser.add_argument("--debug-messages", action="store_true", help='send additional "ninch.at/bot/debug" messages')
    parser.set_defaults(func=lambda: run(handler_factory, **params))

    subparsers = parser.add_subparsers()

    cmd = subparsers.add_parser("accept-invite")
    cmd.add_argument("key", metavar="ACCESS-KEY")
    cmd.set_defaults(func=lambda: utils.accept_invite(args.key, **params))

    args = parser.parse_args()

    if args.identity_file:
        with open(args.identity_file) as f:
            params["identity"] = json.load(f)
    elif "BOT_IDENTITY_JSON" in environ:
        params["identity"] = json.loads(environ["BOT_IDENTITY_JSON"])
    else:
        params["identity"] = {
            "type": environ["BOT_IDENTITY_TYPE"],
            "name": environ["BOT_IDENTITY_NAME"],
            "auth": environ["BOT_IDENTITY_AUTH"],
        }

    if args.debug_messages:
        params["debug_messages"] = True

    loop.run_until_complete(args.func())
