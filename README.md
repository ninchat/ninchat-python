### Overview

- Python library for writing [Ninchat](https://ninchat.com) API clients
- `nincat` utility

### Requirements

- Python 2.6, 2.7 or 3.x
- ws4py package

### Installation

	$ git clone git://github.com/ninchat/ninchat-python.git
	$ cd ninchat-python
	ninchat-python$ git submodule update --init
	ninchat-python$ sudo apt-get install python-ws4py || sudo pip install ws4py
	ninchat-python$ sudo python setup.py install

### Nincat usage

	$ nincat -h
	$ nincat --create-user marv
	$ nincat --join 0gu1nf0c
	$ echo hello world | nincat 0gu1nf0c
	$ nincat --set-email joe.user+bot@example.com
	$ nincat -l
	<frank> good morning

Running without installation:

	ninchat-python$ export PYTHONPATH=
	ninchat-python$ bin/nincat

