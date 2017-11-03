Client support
##############

The ninchat.client.cffi package contains a new client implementation, built
with Go and CFFI.  It's using the same codebase as the ninchat-go and
ninchat-js repositories.

The ninchat.client.legacy package contain an older client implementation, based
on ws4py.


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


Session implementations (legacy)
================================

.. automodule:: ninchat.client.legacy
   :members:

Note: session classes with the same name have the same interface.


Threading
---------

.. automodule:: ninchat.client.legacy.session.thread
   :members:


Gevent interoperability
-----------------------

.. automodule:: ninchat.client.legacy.session.gevent
   :members:


Calling conventions (legacy)
============================


Blocking
--------

.. autoclass:: ninchat.client.legacy.adapter.SyncCallbackAdapter
   :members:
   :inherited-members:

.. autoclass:: ninchat.client.legacy.adapter.SyncQueueAdapter
   :members:
   :inherited-members:


Callbacks
---------

.. autoclass:: ninchat.client.legacy.adapter.AsyncCallbackAdapter
   :members:
   :inherited-members:

.. autoclass:: ninchat.client.legacy.adapter.AsyncQueueAdapter
   :members:
   :inherited-members:

