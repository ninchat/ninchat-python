Client support
##############

The ninchat.client.cffi package contains a new client implementation, built
with Go and CFFI.  It's using the same codebase as the ninchat-go and
ninchat-js repositories.

The ninchat.client.session and ninchat.client.adapter packages contain an older
client implementation, based on ws4py.


Session implementations
=======================


Default
-------

.. automodule:: ninchat.client.cffi
   :members:


Gevent interoperability
-----------------------

.. automodule:: ninchat.client.cffi.gevent
   :members:


Asyncio support
---------------

.. automodule:: ninchat.client.cffi.asyncio
   :members:


Session implementations (old)
=============================

.. automodule:: ninchat.client
   :members:

Note: session classes with the same name have the same interface.


Threading
---------

.. automodule:: ninchat.client.session.thread
   :members:


Gevent interoperability
-----------------------

.. automodule:: ninchat.client.session.gevent
   :members:


Calling convention adapters for old session implementations
===========================================================


Blocking
--------

.. autoclass:: ninchat.client.adapter.SyncCallbackAdapter
   :members:
   :inherited-members:

.. autoclass:: ninchat.client.adapter.SyncQueueAdapter
   :members:
   :inherited-members:


Callbacks
---------

.. autoclass:: ninchat.client.adapter.AsyncCallbackAdapter
   :members:
   :inherited-members:

.. autoclass:: ninchat.client.adapter.AsyncQueueAdapter
   :members:
   :inherited-members:

