Adapters
========

The adapters for the VecNet Cyber Infrastructure was the first attempt to create a single storage backend for all models
which an intelligent data layer that would translate the stored data into relevant data for the models.  The original
model set for the adapters was EMOD and Open Malaria.  These two models required vastly different information to be
appropriately configured and correctly run.

The original attempt for a unified storage layer for the two vastly different models was ultimately abandoned for
the first year of VecNet, but new interest in a unified backend has once again come to the forefront, and the adapters
will most likely be the place to start.

The adapters are designed in a factory, allowing an EMOD or Open Malaria adapter to be created when needed.  Both of
these adapters inherit from a Base Adapter Class, which is an Abstract Base Class (ABC) and can not be instantiated
itself.  Each Adapter then modifies the methods and variables of the Base Class to allow for data in the unified
backend to be used.  The early attempt at this was to take expert opinions on mosquito Bionomics into model specific
mosquito definitions.

*NOTE* The adapters were being developed by Lawrence Selvy and Zachary Torstrick until a decision by Alex Vyushkov (the
Project Lead for the VecNet Cyber Infrastructure) to spread the development to the application developers.  As such, the
consistency of the code after a certain point breaks down.  Further development should take special care not to change
the signatures of the methods in the adapters.  These signatures are used throughout the code, and changing the signature
could cause side effects elsewhere.

Base Adapter
------------

.. autoclass:: data_services.adapters.model_adapter.Model_Adapter
   :members:

EMOD Adapter
------------

Due to the large number of outputs the adapter has a set of golden channels.  These golden channels, listed below, are
the ones that are going to be ingested into the Data Warehouse for each running of the model (replication).  However,
more channels can be ingested later.  These golden channels are only valid for 'MALARIA_SIMS' simulations.

* 228466
* 228480
* 228494
* 228508
* 228522
* 228536
* 228550
* 228564
* 228578
* 228592
* 228441
* 228455
* 228443
* 228451
* 228450
* 228452

.. autoclass:: data_services.adapters.EMOD.EMOD_Adapter
   :members:

Open Malaria Adapter
--------------------

.. autoclass:: data_services.adapters.OM.OM_Adapter
   :members:

Cifer Adapter
-------------

A Cifer adapter was created for the Cifer tool.  The development of this is on hold