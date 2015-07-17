Data API
========

This is the beginning of the replacement for the data adapters.  This, along with model class methods, will eventually
replace the data adapters in total.  This is the location of  new classes, like the Baseline class, that help with
the workflow of the VecNet Cyber Infrastructure Applications.

Baseline
========

As new workflows are created for the Transmission Simulator, a new class that contains all information for a simulation
to run on the cluster is required.  This new class should house binary, json, xml, and configuration files.  There are
three further concepts for the baseline that are important to grasp.

* **Completeness** is obtained when a baseline has all the required files a particular model needs to run on the server
* **Approval** is after a baseline has been run at least once, the outputs of the configuration and all required files
               meets with the creators approval.
* **Version Control** is when a baseline is both complete and approved that it cannot be changed.  Changes are reflected
                      by creating another baseline exactly the same as the first, minus changes.  This allows for a
                      record of changes to grow on a per baseline basis and allow for rollback.  **NOTE: Rollback is
                      not implemented in the Baseline class yet**

There are two baseline classes currently a base class and inherited classes for each model. **Currently only one model
has a baseline, and that's the EMOD model**.

Constructors
------------

.. autoclass:: data_services.data_api.baseline.Baseline

.. automethod:: data_services.data_api.baseline.Baseline.from_dw

.. automethod:: data_services.data_api.baseline.Baseline.from_files

Getters/Setters for files
-------------------------

.. automethod:: data_services.data_api.baseline.Baseline.add_file

.. automethod:: data_services.data_api.baseline.Baseline.add_binfile

.. automethod:: data_services.data_api.baseline.Baseline.add_file_from_string

.. automethod:: data_services.data_api.baseline.Baseline.get_files

.. automethod:: data_services.data_api.baseline.Baseline.get_file_by_id

.. automethod:: data_services.data_api.baseline.Baseline.get_file_by_type

.. automethod:: data_services.data_api.baseline.Baseline.get_file_by_name

.. automethod:: data_services.data_api.baseline.Baseline.get_file

Utility Methods
---------------

Several methods exist on the Baseline class to help select, manage, or examine a Baseline or its state.

.. automethod:: data_services.data_api.baseline.Baseline.save

.. automethod:: data_services.data_api.baseline.Baseline.delete

.. automethod:: data_services.data_api.baseline.Baseline.get_missing_files

.. automethod:: data_services.data_api.baseline.Baseline.get_required_files

.. automethod:: data_services.data_api.baseline.Baseline.list_baselines

Properties/Attributes
---------------------

Properties/attributes can be broken down into two categories.  The first where they describe the state of the baseline,
the second is meta data about the baseline.

Stateful Properties
^^^^^^^^^^^^^^^^^^^

.. autoattribute:: data_services.data_api.baseline.Baseline.has_required_files

.. autoattribute:: data_services.data_api.baseline.Baseline.is_approved

.. autoattribute:: data_services.data_api.baseline.Baseline.is_deleted

.. autoattribute:: data_services.data_api.baseline.Baseline.is_saved

Meta Data Properties
^^^^^^^^^^^^^^^^^^^^
_**NOTE: Due to a bug in sphinx, the class constructor is re-listed here**_

.. autoclass:: data_services.data_api.baseline.Baseline
   :members: id, description, name, location, user, dimbaseline, model, version, required_filetypes

EMOD Baseline
=============

Below is the specific baseline for EMOD.  It shared all of the above methods, properties, getters and setters with the
Baseline class, but adds several convenience methods for EMOD developers.  It also includes specific definitions for
EMOD specific variables, like required_filetypes has EMOD specific file types.  This also checks to make sure that the
data warehouse baseline is of model type EMOD.

.. autoclass:: data_services.data_api.emod_baseline.EMODBaseline
   :members: