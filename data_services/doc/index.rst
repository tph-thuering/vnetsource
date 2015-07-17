Data Services
=============

Data Services is the interface between the VecNet Cyber Infrastructure application code and the VecNet Data Warehouse.
It stands as the data layers where model specific calculations and translations of data are performed.  The tools
can then call upon the API of Data Services to write and read from the Data Warehouse in a secure manner.

The primary focus of Data Services is to provide a consistent interface to the Data Warehouse that secures data based
on the user creating that data.  This is implemented in the database by foreign keys to a user table, which implements
roles in a row by row fashion.

Data Services currently provides a few main interfaces

* **adapter** This was the first attempt at creating a translator from the data storage layer and the application layer.
              There is some model specific functionality, but the majority of the functionality here is corss model and
              is useful for looking up items in the data warehouse.
* **data api** This is the new interface to classes created to help with application workflows, including the self
               updating baseline class.
* **models** These are the Django ORM models required by the application code.  These contain instance and class methods
             that will be useful to developers as they work on the application code.
* **ingesters** These are the model specific ingesters, each ingester is model specific and will take the outputs from
                that specific model and attach the appropriate meta data and store it in the data warehouse.


Table of Contents
-----------------

.. toctree::
   :maxdepth: 1

   adapter
   data_api
   models
   ingesters