"""
This module contains the tests relevant for the pg_utils package in data_services.lib
"""

from struct import pack
import io
import hashlib

from django.test import TestCase
from django.db import connections

from data_services.utils import encode_binary, commit_to_warehouse
from data_services.models import FactData


class PgUtilsTests(TestCase):
    """
    This contains the methods for testing the pg_utils package
    """

    fixtures = ['users.json', 'channels.json']

    def setUp(self):
        """
        This will reset everything required for each test.

        This is run between every test.
        """

        # ---------- Setup the data to be inserted ----------------#
        self.data_hash = "\x83\xcd\x90J\x82v|\xbe\xf7\x01\x92\x14\t\xd8\xc1r"
        data_file = file('data_services/tests/static_files/random_rows.txt', 'r')
        self.data = eval(data_file.read())
        data_file.close()
        self.pg_io = io.BytesIO()
        return

    def test_encode_binary(self):
        """
        This will test the encode binary function.

        This is done by taking a set of test data (read in from file), running it through
        the encode_binary function, and then hashing it.  After which, we compare the
        hashes.  If the hashes are the same, then the encode binary function worked as
        expected.
        """
        print "\nTesting encode_binary"
        pg_io_hash = hashlib.md5()

        for row in self.data:
            self.pg_io.write(encode_binary(*row))

        self.pg_io.seek(0)
        pg_io_hash.update(self.pg_io.read())

        self.assertEqual(
            self.data_hash,
            pg_io_hash.digest(),
            msg="The encoded binary data's hash is different from the expected hash, encoding failed"
        )

        return