"""
This file contains python unit tests for the ReportErrorView in AutoScotty.  They are ran by invoking "manage.py test".
"""

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse


class ReportErrorViewTest(TestCase):
    """
    Contains unit tests for the ReportErrorView.
    """
    def setUp(self):
        """
        This method is called before each test and is responsible for setting up data needed by the tests.
        """
        super(ReportErrorViewTest, self).setUp()
        # create a client for html requests
        self.client = Client()

    def test_invalid_form(self):
        """
        Makes requests with invalid data and ensures the proper response codes and context errors are returned.
        """
        # test no data
        response = self.client.post(reverse('autoscotty_report'))
        self.assertEqual(400, response.status_code)
        #self.assertEqual(response.context['form']['replication'].errors, [u'This field is required.'])
        self.assertEqual(response.context['form']['status'].errors, [u'This field is required.'])
        self.assertEqual(response.context['form']['message'].errors, [u'This field is required.'])
        # test replication not found
        kwargs = {'status': 1, 'message': "Test message here.", 'replication': 100}
        response = self.client.post(reverse('autoscotty_report'), kwargs)
        self.assertEqual(404, response.status_code)

    def test_valid_form(self):
        kwargs = {'status': 1, 'message': "Test message here.", 'replication': 116}
        response = self.client.post(reverse('autoscotty_report'), kwargs)
        self.assertEqual(404, response.status_code)

