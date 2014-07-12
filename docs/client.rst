Client support
##############

.. automodule:: ninchat.client
   :members:


Session implementations
=======================

Note: session classes with the same name have the same interface.


Threading
---------

.. automodule:: ninchat.client.session.thread
   :members:


Gevent interoperability
-----------------------

.. automodule:: ninchat.client.session.gevent
   :members:


Calling conventions
===================


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

