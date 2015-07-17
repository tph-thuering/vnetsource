"""
This file contains python unit tests for the UploadZipView in AutoScotty.  They are ran by invoking "manage.py test".
"""
import hashlib
import os
from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse


class UploadZipTest(TestCase):
    # TODO Add class docstring
    # TODO Add method docstring(s)

    def test_invalid_form(self):
        # setup Client and test data
        c = Client()
        f = open(os.path.join(os.path.dirname(__file__), 'autoscottytest-7613.zip'), 'rb')
        h = hashlib.sha1()
        h.update(f.read())
        f.seek(0)

        # test no data
        response = c.post(reverse('autoscotty_upload'))
        self.assertEqual(400, response.status_code)
        self.assertEqual(response.context['form']['zip_file'].errors, [u'This field is required.'])
        self.assertEqual(response.context['form']['zip_file_hash'].errors, [u'This field is required.'])
        self.assertEqual(response.context['form']['model_type'].errors, [u'This field is required.'])

        # test hash mismatch
        kwargs = {'zip_file': f, 'zip_file_hash': 'abc', 'sync': True, 'model_type': 'EMOD'}
        response = c.post(reverse('autoscotty_upload'), kwargs)
        self.assertEqual(460, response.status_code)
        self.assertEqual(response.context['form'].errors['hash_mismatch'], [u'The hash does not match the file.'])

    def test_valid_form(self):
        # setup Client and test data
        c = Client()
        f = open(os.path.join(os.path.dirname(__file__), 'autoscottytest-7613.zip'), 'rb')
        h = hashlib.sha1()
        h.update(f.read())
        f.seek(0)

        kwargs = {'zip_file': f, 'zip_file_hash': h.hexdigest(), 'sync': False, 'model_type': 'EMOD'}
        response = c.post(reverse('autoscotty_upload'), kwargs)
        self.assertEqual(200, response.status_code)