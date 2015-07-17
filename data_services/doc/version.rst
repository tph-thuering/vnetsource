Version
=======

.. automodule:: data_services.version
   :members:


History
-------

Version 1.5, release 00 (20 Nov 2014)

* Depricated support for hstore-based DimRuns and DimExecutions

Version 1.4, release 05 (14 Oct 2014)

* Added model_version to DimRun, DimBaseline and DimTemplate
* Added emod_id.py (EMOD model IDs for v1.5 and v1.6.1)

Version 1.4, release 04 (11 Oct 2014)

* Removed reference to job_services.models.Manifest

Version 1.4, release 03 (8 Oct 2014)

* Disabled creation of new DimBaseline "versions"

Version 1.4, release 02 (6 September 2014)

* Removed get_job_priority, save_run_from_config, get_config_from_run and fetch_interventions functions
* Removed RunConfig class

Version 1.4, release 01 (27 August 2014)

* DimRun.set_input_files now takes a dictionary of files rather that a list

Version 1.3, release 05 (17 August 2014)

* Added "vecnet_fill_location_from_point" function to DimLocation (it replaces stored procedure
vecnet_fill_location_from_point) and registered DimLocation model in Django admin panel.

Version 1.3, release 04 (17 August 2014)

* Removed UserExperimentPermissions and GroupExperimentPermissions models (unused)

Version 1.3, release 03 (17 August 2014)

* Removed GisAdm007, GisAdm1Lev, GisAdm2Lev, GisAdm3Lev model. All queries should go directly to GisBaseTable model.
This is done as a preparation for removing partition on gis_base_table

Version 1.3, release 02 (13 August 2014)

* Removed LocationsHierarchy class (unused)

Version 1.3, release 01 (__ August 2014)

* Changed DimTemplate models - added climate_url, climate_start_date and climate_end_date. This is necessary to refactor
fetch_locations function in Model_Adapter

Version 1.2, release 01 (20 July 2014)

* Added API for working with sweep in DimRun (has_sweeps and get_sweeps)

Version 1.2, release 01 (20 July 2014)

* DimBinFile object can now be represented as file-like object

Version 1.1, release 01 (14 July 2014)

* Added REST API access to input files stored in DimBinFiles table.

Version 1.0, release 07 (13 July 2014)

* Removed broken test data_services.ingester_tests.OpenMalariaIngestTest (Problem: KeyError: "There is no item named u'test_ingest\\\\test_ingest-000.0.xml' in the archive")

Version 1.0, release 06 (10 July 2014)

* Fixed test data_services.EmodIngestTest.test_bad_simulation_ingest

Version 1.0, release 05 (07 July 2014)

* Fixed broken testdata_services.tests.model_adapter_tests.SaveRunTests.test_save_run_return_obj - for real this time

Version 1.0, release 04 (06 July 2014)

* Fixed broken testdata_services.tests.model_adapter_tests.SaveRunTests.test_save_run_return_obj

Version 1.0, release 03 (05 July 2014)

* Added version.rst
* Removed broken test data_services.tests.pg_utils_tests.test_commit_to_warehouse (Problem: TypeError: commit_to_warehouse() takes exactly 4 arguments (3 given))
* Removed broken test data_services.tests.model_adapter_tests.RunExpansionTest (Problem: no such file data_services/tests/static_files/changeDoc.json)

Version 1.0, release 02

* Initial version