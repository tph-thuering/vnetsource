Ingesters
---------

These perform Extraction, Transformation, and Loading of simulation output files for both models (EMOD and Open Malaria)
into the VecNet Cyber Infrastructure's Data Warehosue.  Since each type of model has very specific output specifications,
the ingesters are built off of a Base ingester class where any shared functionality resides.  Any model specific
functionality resides in the model specific ingester, discussed below.

It is important to note that although these ingesters take advantage of the Django ORM, that they do no mass ingestion
using that ORM.  The reason is that for bulk ingestion, it was seen that if the process thread continues on after the
mass ingestion that a memory leak is formed, and the bulk ingestion process slows down dramatically.  Even though no
evidence was found that the data inserted via this process is corrupted, it was seen that a new method to ingest massive
amounts of data (> 1 M rows) was needed.

Using the ``PostgreSQL`` documentation found `here <http://www.postgresql.org/docs/9.3/static/sql-copy.html>`_, the process
extracts data from the source files, transforms them into the binary representations that ``PostgreSQL`` uses to store
information in its tables, and then loads it via the ``COPY`` command.  This reduced the ingestion time for > 4 M rows
of data from ~8 minutes to < 1 minute.  The gain in efficiency was seen as reason to keep such a complicated data ingestion
process in place.

Base Ingester
^^^^^^^^^^^^^

This base ingester is an Abstract Base Class and should not be instantiated.  Other ingesters should inherit from this
as it contains useful functionality.  For instance, the base class is where a temporary file and directory can be created
in an Operating System agnostic way (the python library responsible for this understands the temporary files directories
on each OS).  This also has important clean up functionality once an ingester has completed.

.. autoclass:: data_services.ingesters.base_ingester.Base_ingester
   :members:

EMOD Ingester
^^^^^^^^^^^^^

This ingester works on a per execution basis, ingesting all replications of a particular execution (single realization of
configurations).  It also ensures that if data already exists for a particular replication for a particular channel, that
the data that already exists in the Data Warehoue _**WILL NOT BE CLOBBERED**_.  This means that pre-existing data takes
priority over new data.  Each particular file type is parsed in this fashion.

.. autoclass:: data_services.ingesters.EMOD_ingest.EMOD_ingester

Open Malaria Ingester
^^^^^^^^^^^^^^^^^^^^^

This ingester was the first to ingest by execution, ingesting and creating replications as needed.  It does this by using
two classes, the first is the execution ingester, the second is the replication ingester.  In this manner the execution
ingester loops over replications, instantiating replication ingesters as needed.

Open Malaria output is closely linked with its input, therefore the configuration file _**MUST BE PRESENT DURING
INGESTION**_.  A library, build by Shawn Brown of the Pittsburgh Super Computing (PSC) development team is what is used
to parse the input and output files to get appropriate channels.

For each replication, the input is parsed out and channels are calculated from positional arguments in the input.  Once
this is finished, the ingester checks against the Data Warehouse to ensure pre-existing data is not clobbered.  This
particular ingester is prone to failure if things change significantly in the input file.

This error-proneness is caused by the PSC Parsing library, and is in need of refactoring.

Execution Ingester
""""""""""""""""""

.. autoclass:: data_services.ingesters.OM_ingester.OM_Ingester

Replication Ingester
""""""""""""""""""""

.. autoclass:: data_services.ingesters.OM_ingester.OpenMalaria_ingester

