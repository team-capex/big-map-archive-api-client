.. _bma:

.. module:: bma


===========================================
BIG-MAP Archive API
===========================================
The :class:`~big_map_archive_api.api.BMA` is main class for the API.

Upload and publish records
============================
Suppose all the records data are saved in the ``records`` folder. Each record should has a ``metadata.json`` file to save all its metadata.


Upload records:

.. code-block:: python

    from big_map_archive_api.api import BMA
    token = "Your Token"
    bma = BMA(token=token)
    bma.upload_records("records")

Publish records:

.. code-block:: python

    bma.publish()



List of all Methods
===================

.. autoclass:: big_map_archive_api.api.BMA
   :members:
