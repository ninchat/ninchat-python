Session client support
######################

The ninchat.client package contains a client implementation built using Go and
CFFI (the _ninchat_cffi module).  It's using the same codebase as the
ninchat-go and ninchat-js repositories.


Session implementations
=======================


Default
-------

.. automodule:: ninchat.client
   :members:


Gevent interoperability
-----------------------

.. automodule:: ninchat.client.gevent
   :members:


Asyncio support
---------------

.. automodule:: ninchat.client.asyncio
   :members:
