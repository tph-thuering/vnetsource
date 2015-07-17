########################################################################################################################
# VECNet CI - Prototype
# Date: 4/5/2013
# Institution: University of Notre Dame
# Primary Authors:
#   Lawrence Selvy <Lawrence.Selvy.1@nd.edu>
#   Zachary Torstrick <Zachary.R.Torstrick.1@nd.edu>
########################################################################################################################

"""
This module contains custom exceptions for the ETL script.
"""

class TableDoesNotExist(Exception):
    """
    This class defines a custom exception. This exception is thrown in the ETL script when
    a database table with the given name cannot be found.
    """
    
    pass

