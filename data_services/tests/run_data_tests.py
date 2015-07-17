"""
This module contains the tests relevant for the pg_utils package in data_services.lib
"""


from django.test import TestCase
from data_services.utils.run_data import RunData
from django.core.exceptions import ObjectDoesNotExist

class RunDataTests(TestCase):
    """
    This contains the methods for testing the pg_utils package
    """

    fixtures = ['users.json', 'channels.json']

    def setUp(self):
        """
        This will reset everything required for each test.

        This is run between every test.
        """

        return

    def test(self):
        """
        Testing exceptions raised if input parameters are wrong
        """

        self.assertRaises(NameError, RunData)
        self.assertRaises(TypeError, RunData, {"execution":dict()})
        self.assertRaises(ObjectDoesNotExist, RunData, {"execution":4096})
        #self.assertRaises(ObjectDoesNotExist, RunData, {"execution":4096,"channel":"non-existing channel"})

        return