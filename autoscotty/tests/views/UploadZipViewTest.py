"""
This file contains python unit tests for the UploadZipView in AutoScotty.  They are ran by invoking "manage.py test".
"""
import hashlib
import os
from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import SimpleUploadedFile


class UploadZipViewTest(TestCase):
    """
    Contains unit tests for the UploadZipView.
    """
    def setUp(self):
        """
        This method is called before each test and is responsible for setting up data needed by the tests.
        """
        super(UploadZipViewTest, self).setUp()
        # create a client for html requests
        self.client = Client()
        # open a file and create a file object
        tmp_file = open(os.path.join(os.path.dirname(__file__), 'autoscottytest-7613.zip'), 'rb')
        self.zip_file = SimpleUploadedFile(tmp_file.name, tmp_file.read())
        # reset the file and create a hash, then close the file
        tmp_file.seek(0)
        self.hash = hashlib.sha1()
        self.hash.update(tmp_file.read())
        tmp_file.close()

    def tearDown(self):
        """
        This method is called after a test runs. It does any cleanup necessary, such as closing files.
        """
        if self.zip_file:
            self.zip_file.close()

    def test_invalid_form(self):
        """
        Makes requests with invalid data and ensures the proper response codes and context errors are returned.
        """
        # test no data
        response = self.client.post(reverse('autoscotty_upload'))
        self.assertEqual(400, response.status_code)
        self.assertEqual(response.context['form']['zip_file'].errors, [u'This field is required.'])
        self.assertEqual(response.context['form']['zip_file_hash'].errors, [u'This field is required.'])

        # test hash mismatch
        kwargs = {'zip_file': self.zip_file, 'zip_file_hash': 'abc', 'sync': True}
        response = self.client.post(reverse('autoscotty_upload'), kwargs)
        self.assertEqual(460, response.status_code)
        self.assertEqual(response.context['form'].errors['hash_mismatch'], [u'The hash does not match the file.'])

    def test_valid_form(self):
        """
        Performs a request with a valid form and checks for the proper response.
        """
        kwargs = {'zip_file': self.zip_file, 'zip_file_hash': self.hash.hexdigest(),
                  'sync': False, 'model_type': 'EMOD'}
        response = self.client.post(reverse('autoscotty_upload'), kwargs)
        self.assertEqual(200, response.status_code)