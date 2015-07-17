API
===

This document describes how VecNet tools interact with this system component.

Submitting Simulations
----------------------
.. autofunction:: job_services.dispatcher.submit


.. _cluster-IDs:

Cluster IDs
^^^^^^^^^^^
Use one of these ID constants when calling the :py:func:`~job_services.dispatcher.submit` function to specify a
particular computing cluster:

.. autodata:: job_services.cluster_id.PSC_LINUX

.. autodata:: job_services.cluster_id.ND_WINDOWS

For example::

  import job_services.dispatcher
  from job_services import cluster_id

  success, message = job_services.dispatcher.submit(run, user, cluster=cluster_id.PSC_LINUX)

There is a special ID that instructs the dispatcher to automatically select a cluster based on various factors.

.. autodata:: job_services.cluster_id.AUTO

Such factors include:

*  which simulation model will be run (a cluster may only support a subset of the available simulation models; for
   example, EMOD only runs on Windows).
*  who the user is and their organization (a cluster may only be available to a subset of users; for example, only
   developers may access a test cluster).
*  the user's job quotas and how much of those quotas is available (for example, has a user reached their monthly job
   quota on a particular cluster?).
*  cluster availability (i.e., load balancing).

Although the auto-select algorithm could eventually evolve to consider all these factors, its current implementation
simply selects the default cluster (ND Windows development cluster).


Querying Status
---------------
.. autofunction:: job_services.dispatcher.get_status

Status information
^^^^^^^^^^^^^^^^^^
.. autoclass:: job_services.api.Status
   :members:


API Errors
----------
.. autoclass:: job_services.api.ApiErrors


.. include:: /docs/django-links.rst
