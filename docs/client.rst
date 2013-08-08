Client support
##############

.. automodule:: ninchat.client
   :members:


Session implementations
=======================

Note: session classes with the same name have the same interface.


Threading
---------

.. automodule:: ninchat.client.thread
   :members:


Gevent interoperability
-----------------------

.. automodule:: ninchat.client.gevent
   :members:


Calling conventions
===================


Blocking
--------

.. autoclass:: ninchat.client.call.SyncCallbackAdapter
   :members:
   :inherited-members:

.. autoclass:: ninchat.client.call.SyncQueueAdapter
   :members:
   :inherited-members:


Callbacks
---------

.. autoclass:: ninchat.client.call.AsyncCallbackAdapter
   :members:
   :inherited-members:

.. autoclass:: ninchat.client.call.AsyncQueueAdapter
   :members:
   :inherited-members:

