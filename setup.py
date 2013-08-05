import sys
from distutils.core import setup

setup(
	name             = "ninchat-python",
	version          = "1.0-pre",
	maintainer       = "Timo Savola",
	maintainer_email = "timo@ninchat.com",
	url              = "https://github.com/ninchat/ninchat-python",
	scripts          = ["bin/nincat"],

	packages = [
		"ninchat",
		"ninchat/api",
		"ninchat/api/messages",
		"ninchat/api/spec/json",
		"ninchat/client",
		"ninchat/client/session",
		"ninchat/client/session/websocket",
	],

	package_data = {
		"ninchat/api/spec/json": ["*.json", "*/*.json"],
	},

	classifiers = [
		"Development Status :: 4 - Beta",
		"Environment :: Console",
		"Intended Audience :: Developers",
		"Intended Audience :: System Administrators",
		"License :: OSI Approved :: BSD License",
		"Operating System :: OS Independent",
		"Programming Language :: Python",
		"Programming Language :: Python :: 2",
		"Programming Language :: Python :: 2.6",
		"Programming Language :: Python :: 2.7",
		"Programming Language :: Python :: 3",
		"Topic :: Communications",
		"Topic :: Communications :: Chat",
		"Topic :: Communications :: Conferencing",
		"Topic :: Internet",
		"Topic :: Internet :: WWW/HTTP",
		"Topic :: Software Development :: Libraries :: Python Modules"
	],
)
