Models
======

These are the Django ORM models used to communicate with the VecNet CyberInfrastructure Data Warehouse.  Each model
can be broken down into Dimension models, Fact models, and GIS Models.  Each grouping matches a table grouping in the
Data Warehouse (DW).  Below is a table containing the three letter prefix of the model and what that prefix means:

======  ================================================================================================================
Prefix  Meaning
======  ================================================================================================================
Dim     This is a dimension table.  This contains meta data information about a fact, like the when and where.  Some
        examples are DimLocation or DimUser.  These are not 'facts' of themselves, but data used to qualify the fact.
Fact    These are the aggregate-able pieces of information of interest.  These are things like demographics, weather,
        etc.  The guideline is that if its something that needs to be aggregated, its probable a fact.
GIS     GIS Tables are those that are requiring a special gis model.  These are where shapes are stored for GIS lookups.
        These types of lookups are largely not needed as the GIS table is not a hierarchical table that contains all the
        _within_ and _contains_ type GIS queries.
======  ================================================================================================================

API
---

Below each model that is available is listed along with all members for that class.  Each class can have class methods
or static methods to help developers employ the data storage layer in their views/applications.

.. automodule:: data_services.models
   :members:
