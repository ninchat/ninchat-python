### Overview

- Python library for writing [Ninchat](http://ninchat.com) API clients
- `nincat` utility

### Requirements

- Python 2.6, 2.7 (for library and nincat) or 3.x (for library)
- ws4py

### Installation

	# pip install ws4py
	# python setup.py install

### Nincat usage

	$ nincat -h
	$ nincat --create-user marv
	$ nincat --join 0gu1nf0c
	$ echo hello world | nincat 0gu1nf0c
	$ nincat --set-email joe.user+bot@example.com
	$ nincat -l
	<frank> good morning

Running in source tree without installation:

	$ export PYTHONPATH=
	$ bin/nincat

