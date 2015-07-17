"""
This contains the JCDField class which is used in the
DimRun and DimExecution models.

This will store a JCD in the data warehouse and parse a
JCD from the data warehouse.
"""
from django.core.exceptions import ValidationError
from django.db import models
from change_doc import JCD


class JCDField(models.TextField):
    """
    This is the field class for the JCD.

    This will allow the storage and recalling of the JSON Change document from and to a python object
    representation.
    """
    # TODO: Write tests

    description = "JSON Change Document for the VecNet-CI"

    __metaclass__ = models.SubfieldBase

    def db_type(self, connection):
        """
        This defines the database type.  In PostgreSQL 9.3, the type is JSON, which will be used as
        a text field.

        *This breaks database agnosticism as other databases do not have a JSON type*
        """
        return 'json'

    def to_python(self, value):
        """
        This converts data from the database (Stored in a JSON field, but accessed as a TextField) as a JCD
        object.

        As per the django docs, we are dealing with three common argument types for value.
            - An instance of the correct type (JCD)
            - A string
            - What the database returns  (which is a dict)

        Since we allow the value in the database to be null, we also prepare for the case where the JCD is None
        """
        if isinstance(value, JCD):
            return value

        if isinstance(value, (str, unicode)):
            return JCD.from_json(value)

        if value is None:
            return None

        if isinstance(value, dict):
            return JCD(jcd=value)

        raise ValidationError("Invalid input for JCD instance")

    def get_prep_value(self, value):
        """
        This is how we pack up the JCD into a form the database can understand
        """
        if value is None:
            return None
        else:
            return value.json

    def get_prep_lookup(self, lookup_type, value):
        """
        This is how the lookups for this field are defined.

        We may implement these in the future (for instance to help with previously generated data); however,
        for now there are no lookups available for this field type.
        """
        raise TypeError("No Lookups are available for the JCD Field")

    def value_to_string(self, obj):
        """
        This creates a string from the value of the JCD object
        """
        value = self._get_val_from_obj(obj)
        return self.get_prep_value(value)