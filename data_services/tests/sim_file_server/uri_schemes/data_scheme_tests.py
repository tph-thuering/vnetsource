import re
from urlparse import urlparse

from .handler_tests import SchemeHandlerTests
from ..test_util import OpenMalariaData
from ....sim_file_server.uri_schemes.data_scheme import DataSchemeHandler, PATH_PREFIX


class CustomHandler(DataSchemeHandler):
    """
    A wrapper around a data scheme handler, so we can do additional checks on the URIs it returns from its store_file
    method.
    """

    def __init__(self, new_uri_validator):
        """
        Initialize a new instance.

        :param callable uri_validator: The object that performs additional checks on the URIs returned by the store_file
                                       method.
        """
        super(CustomHandler, self).__init__()
        assert callable(new_uri_validator)
        self.new_uri_validator = new_uri_validator

    def store_file(self, contents):
        """
        Call the equivalent method in the real handler, then perform some checks on the URI returned.
        """
        uri, md5 = super(CustomHandler, self).store_file(contents)
        self.new_uri_validator(uri)
        return uri, md5


class DataSchemeHandlerTests(SchemeHandlerTests):
    """
    Tests for the data scheme handler.
    """

    def validate_new_uri(self, new_uri):
        """
        Check that a new URI returned the scheme handler's store_file method is properly formatted.
        """
        parsed_uri = urlparse(new_uri)
        self.assertTrue(parsed_uri.scheme, 'data')
        self.assertTrue(parsed_uri.path.startswith(PATH_PREFIX))

        # Confirm that the path component got all the encoded data
        self.assertEqual(parsed_uri.query, '')
        self.assertEqual(parsed_uri.fragment, '')

        # Make sure the path after the prefix contains just printable characters (spaces excluded), i.e., no control
        # characters (\x00 to \0x1f, and 0x7f), spaces (\x20), or non-ASCII characters (\x80 - \xff).
        path_after_prefix = parsed_uri.path[len(PATH_PREFIX):]
        self.assertTrue(re.match(r'^[\x21-\x7e]*$', path_after_prefix))

        # Per section 2.2 of RFC 3896 -- http://tools.ietf.org/html/rfc3986#section-2.2
        # Make sure there are no reserved characters in the URI's path after the prefix
        gen_delims  = ":/?#[]@"
        sub_delims  = "!$&'()*+,;="
        reserved = gen_delims + sub_delims
        reserved_pattern = re.compile('[%s]' % reserved.replace('[', '\\[').replace(']', '\\]'))
        self.assertFalse(re.search(reserved_pattern, path_after_prefix))

    def get_handler(self):
        return CustomHandler(self.validate_new_uri)

    def test_read_unsafe_uris(self):
        """
        Test that the handler still supports the reading of unsafe URIs that already exist in the databases.
        """
        handler = self.get_handler()
        for contents in (OpenMalariaData.EMPTY_SCENARIO, OpenMalariaData.CTSOUT_TXT):
            unsafe_uri = 'data:,' + contents
            retrieved_contents = self.get_file_contents(handler, unsafe_uri)
            self.assertEqual(retrieved_contents, contents)
