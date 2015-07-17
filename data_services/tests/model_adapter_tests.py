"""
This is the model_adapter test case.  This houses all of the model_adapters test cases
and will eventually house all model adapter test cases.
"""

from django.test import TestCase
from data_services.models import DimUser

from data_services.adapters import EMOD_Adapter

def create_valid_user():
    return DimUser.objects.create(pk=2,  # adapter assumes valid users have pk != 1
                                  username='test user')

