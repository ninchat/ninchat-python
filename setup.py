import os

if not os.path.exists("ninchat/api/spec/json"):
	raise Exception("ninchat-api submodule not found")

try:
	import setuptools
	import sys

	def setup(**kwargs):
		with open("requirements.txt") as file:
			lines = file.read().strip().split("\n")
			if getattr(sys, "subversion", [None])[0] != "CPython" or sys.version_info[0] != 2:
				lines = [l for l in lines if "!cpython2" not in l]

		setuptools.setup(install_requires=lines, **kwargs)

except ImportError:
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
