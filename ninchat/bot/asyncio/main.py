import argparse
import asyncio
import json
from collections import defaultdict
from os import environ

from . import run
from . import utils

loop = asyncio.get_event_loop()


class Handler:

    def __init__(self, queue):
        self.queue = queue
        self.nums = defaultdict(int)

    def on_begin(self, user_id):
        self.nums[user_id] = 0
        return "Hello! " + str(self.nums[user_id])

    def on_messages(self, user_id, messages):
        self.nums[user_id] += 1
        return 'Really, "' + "\n".join(messages) + '"? ' + str(self.nums[user_id])

    def on_close(self, user_id):
        try:
            del self.nums[user_id]
        except KeyError:
            pass


def main(handler_factory=Handler, *, identity_file=None):
    args = None
    params = {}

    parser = argparse.ArgumentParser()
    parser.add_argument("--identity-file", metavar="PATH", default=identity_file, help='JSON document containing "type", "name" and "auth" properties')
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

    loop.run_until_complete(args.func())
