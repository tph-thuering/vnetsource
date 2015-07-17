Version
=======

.. automodule:: job_services.version
   :members:


History
-------
Version 2.2, release 01 (16 October 2014)

* Added support for model_version field in DimRun. Different EMOD model will be invoked for different model_version fields

Version 2.2, release 00 (14 October 2014)

* Switched to using cluster_scripts v1.3 (start_simgroup.py and start_simulation.py)

Version 2.1, release 02 (09 September 2014)

* Prettyfied Quota class in django admin panel
* Fixed two broken tests

Version 2.1, release 01 (30 June 2014)

* BASE_DIR in psc_submit_manifest function is now configurable by JOB_SERVICES_BASE_DIR configuration option
* Moved cluster_scripts to a separate repository
* Removed WinHpcProvider (PROTOTYPE provider)
* Added Quota object to job_services admin panel

Version 2.0, release 02 (23 April 2014)

* Updated the WinHPC manifest provider to work with the fix for bug #5603.

Version 2.0, release 01 (08 April 2014)

* A new error handling scheme has been introduced.
* Increased unit test coverage
* Cluster side scripts were refactored to be more configurable
* Non manifest provider was deprecated
* The winhpc license and winhpc files were added and moved to a new folder
* Providers can now be configured for multiple clusters
* Documentation was update, including the addition of a purpose statement

Version 1.1, release 01 (05 March 2014)

* Unit tests have been updated to make better use of the mock  library, as well as updated to use better testing
  techniques.
* Several internal functions have been refactored and moved to different modules
* Documentation has been improved, and there's now a version class to facilitate checking the version
* The non-support of Open Malaria jobs is now handled gracefully
* Provider selection is configurable to allow easily testing out new providers
* Checks to prevent submitting the same run twice exist
* The release process has been documented.

Version 1.0, release 01 (13 February 2014)

* Currently only supports the submission of EMOD simulations.
* Two initial providers have been implemented:

  * PROTOTYPE provider -- uses the current job submission functionality in data services' EMOD model adapter:
    (the ``launch_run`` method in the ``data_services.adapters.EMOD.EMOD_Adapter`` class).
  * MANIFEST_PROTOTYPE provider -- uses the new manifest-based job submission code in this component:
    (the ``job_services.launch.beta_launch_run`` function).

* The provider selection for the DEFAULT cluster uses the PROTOTYPE provider unless the caller explicitly requests
  manifest submission.
* Two types of job quotas have been implemented:

  * ``max per run`` -- The maximum number of jobs for a single model run.
  * ``max per month`` -- The maximum number of jobs that a user can submit in a single month.