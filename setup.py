from os import environ, getcwd
from os.path import exists, join

if not exists("ninchat/api/spec/json"):
    raise Exception("ninchat-api submodule not found")

if not exists("go/src/github.com/ninchat/ninchat-go/include"):
    raise Exception("ninchat-go submodule not found")

environ["GOPATH"] = join(getcwd(), "go")

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
    name="ninchat-python",
    version="1.0rc0",
    maintainer="Timo Savola",
    maintainer_email="timo@ninchat.com",
    url="https://github.com/ninchat/ninchat-python",
    scripts=["bin/nincat"],
    setup_requires=["cffi>=1.0.0"],
    cffi_modules=["build_cffi.py:ffibuilder"],

    packages=[
        "ninchat",
        "ninchat/api",
        "ninchat/api/messages",
        "ninchat/api/spec/json",
        "ninchat/client",
        "ninchat/client/cffi",
        "ninchat/client/session",
    ],

    package_data={
        "ninchat/api/spec/json": ["*.json", "*/*.json"],
    },

    classifiers=[
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
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Communications",
        "Topic :: Communications :: Chat",
        "Topic :: Communications :: Conferencing",
        "Topic :: Internet",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
)
