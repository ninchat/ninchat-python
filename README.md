### Overview

- Python library for writing [Ninchat](https://ninchat.com) API clients
- `nincat` utility

### Requirements

- Python 2.6, 2.7 or 3.x
- ws4py package
- PyCrypto package (for secure metadata)

### Installation

	$ pip install git+https://github.com/ninchat/ninchat-python.git

Source checkout:

	$ git clone https://github.com/ninchat/ninchat-python.git
	$ cd ninchat-python
	ninchat-python$ git submodule update --init
	ninchat-python$ sudo apt-get install python-ws4py python-crypto || sudo pip install -r requirements.txt
	ninchat-python$ sudo python setup.py install

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

