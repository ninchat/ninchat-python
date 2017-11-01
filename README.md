[![status](https://travis-ci.org/ninchat/ninchat-python.svg)](https://travis-ci.org/ninchat/ninchat-python)

### Overview

- Python library for writing [Ninchat](https://ninchat.com) API clients etc.
- `nincat` utility

### Requirements

- Python 2.6, 2.7 or 3.x
- [cryptography](https://cryptography.io) or PyCrypto (for secure metadata)
- cffi and [Go compiler](https://golang.org) (for API client)
- ws4py (for legacy API client)

### Installation

	$ pip install git+https://github.com/ninchat/ninchat-python.git

Source checkout:

	$ git clone --recurse-submodules https://github.com/ninchat/ninchat-python.git
	$ cd ninchat-python
	ninchat-python$ sudo apt install python3-cryptography python3-cffi golang-go || sudo pip install -r requirements.txt
	ninchat-python$ sudo python3 setup.py install

### Nincat usage

	$ nincat -h
	$ nincat --create-user marv
	$ nincat --join 0gu1nf0c
	$ echo hello world | nincat 0gu1nf0c
	$ nincat --set-email joe.user+bot@example.com
	$ nincat -l
	<frank> good morning

Running from source tree:

	ninchat-python$ export PYTHONPATH=
	ninchat-python$ bin/nincat

