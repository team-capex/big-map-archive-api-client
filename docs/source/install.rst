.. _download_and_install:

===========================================
Installation
===========================================

The simplest way to install the api is to use pip.

.. code-block:: console

    pip install --upgrade --user big-map-archive-api


Configuration
==================


- Step 1: You need a personal API access token. If you do not have one yet, follow this link after a successful login: https://archive.big-map.eu/account/settings/applications/tokens/new/.
- Step 2: Setup the token for API by running:

.. code-block:: console

    $ bma_api add-token
    Your token: []:



.. note::
   You can skip step2, and then add you token in the Python script directly.
