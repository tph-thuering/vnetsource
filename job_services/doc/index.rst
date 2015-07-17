Job Services
============

Overview
--------
Job Services is a comprehensive submission system for the VecNet CI. It aims to provide a common API
(application programming interface) that the CI tools can use to communicate with clusters. The two primary functions
of Job Services are:

* **job submission**: Tools can use the API to submit a job to the cluster for processing.
* **querying job status**: Tools can query the status of a submitted job, and then display that status to the user(s).

Job Services provides a number of benefits, including:

* **abstraction**: Tools can submit a job without worrying about factors such as quotas and load-balancing. Instead,
  Job Services is responsible for determining which cluster to submit a job to, and whether or not a cluster is
  available for a given user and run.
* **common interface**: Using a common interface allows for quicker, more modular development.
* **extensibility**: Job Services was designed to quickly and easily accommodate new clusters and simulation models.
* **versions**: Job Services uses a (documented) version system so developers know what to expect from the api.


Table of Contents
-----------------
.. toctree::
   :maxdepth: 1

   api
   conf
   internals
   version