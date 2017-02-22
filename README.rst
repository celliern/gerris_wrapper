gerris wrapper
==========================

This little library has been written in order to run gerris simulation in linux and windows with the use of docker image in a thread-safe way.

The main goal is to ensure a stable behaviour across platform and easier way to run the simulations.

Install
=======

For now, the package is available on PyPI, and via the github repo.

.. code:: shell

    pip install gerris-wrapper
    pip install git+git://github.com/celliern/gerris_wrapper.git

this package works well when docker is properly installed and configured (https://www.docker.com/products/docker).

Docker images
=============

The gerris docker image is available on the docker hub repository celliern/gerris. It is built with mpi support.

Usage
=====

very simple use:

.. code:: python

    from gerris_wrapper import run
    result = run('in.gfs')

API
===

TODO
====

.. Credits
.. -------
