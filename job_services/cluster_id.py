"""
The ID constants for all known clusters.
"""

# This module has no import statements, so it can be safely used in a Django project settings file.

# Short strings are used to facilitate debugging
AUTO = 'auto'            #: Automatically select the cluster
PSC_LINUX = 'PSC lin'    #: Linux cluster at Pittsburgh Supercomputer Center
ND_WINDOWS = 'ND win'    #: Windows cluster at University of Notre Dame

ALL_KNOWN = (AUTO, PSC_LINUX, ND_WINDOWS)  #: List of all known IDs.
_set_of_all_known = set(ALL_KNOWN)

MAX_LENGTH = 7  #: For use when storing IDs in a database field, e.g. (CharField(max_length=cluster_id.MAX_LENGTH)


def is_valid(id_):
    """
    Is an ID a known value?

    :returns: True or False
    :raises: TypeError is id_ is not a string
    """
    if not isinstance(id_, basestring):
        raise TypeError('Expected string or unicode')
    return id_ in _set_of_all_known


def parse(text):
    """
    Parse a cluster ID from a text string.
    Handles both unicode or ASCII strings.
    Leading and trailing whitespace is ignored.
    Letter case is also ignored.

    :returns: a cluster ID or None if the string isn't a valid ID.
    """
    text_lower = text.strip().lower()
    for id_ in ALL_KNOWN:
        if text_lower == id_.lower():
            return id_
    return None


class TestingApi(object):
    """
    API for unit tests to enable and disable the mock cluster id.
    """
    MOCK_ID = "mock"
    _ALL_KNOWN_ORIGINAL = ALL_KNOWN

    @staticmethod
    def enable_mock_id():
        """
        Enable the mock cluster id.
        """
        global ALL_KNOWN, _set_of_all_known
        ALL_KNOWN = TestingApi._ALL_KNOWN_ORIGINAL + (TestingApi.MOCK_ID,)
        _set_of_all_known = set(ALL_KNOWN)

    @staticmethod
    def disable_mock_id():
        """
        Disable the mock cluster id.
        """
        global ALL_KNOWN, _set_of_all_known
        ALL_KNOWN = TestingApi._ALL_KNOWN_ORIGINAL
        _set_of_all_known = set(ALL_KNOWN)
