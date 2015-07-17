from django.test import TestCase
from .. import cluster_id


class ClusterIdTests(TestCase):
    """
    Unit tests for cluster_id module.
    """

    def test_max_length(self):
        """
        Verify that all known id constants fit within the maximum length.
        """
        for id_ in cluster_id.ALL_KNOWN:
            self.assertTrue(len(id_) <= cluster_id.MAX_LENGTH)

    def test_is_valid_with_all_known(self):
        """
        Test the is_valid function with each of the known id constants.
        """
        for id_ in cluster_id.ALL_KNOWN:
            self.assertTrue(cluster_id.is_valid(id_))

    def test_is_valid_with_bad_ids(self):
        """
        Test the is_valid function with bad ID strings.
        """
        self.assertFalse(cluster_id.is_valid("foo"))
        self.assertFalse(cluster_id.is_valid(u"foo"))
        self.assertFalse(cluster_id.is_valid(""))

    def test_is_valid_with_wrong_type(self):
        """
        Test the is_valid function with wrong data types.
        """
        self.assertRaises(TypeError, cluster_id.is_valid, None)
        self.assertRaises(TypeError, cluster_id.is_valid, 7)
        self.assertRaises(TypeError, cluster_id.is_valid, dict())
        self.assertRaises(TypeError, cluster_id.is_valid, [cluster_id.AUTO])
        self.assertRaises(TypeError, cluster_id.is_valid, cluster_id.ALL_KNOWN)


class MockClusterIdTests(TestCase):
    """
    Unit tests for mock cluster id.
    """

    def test_enable_mock_id(self):
        """
        Test the enable_mock_id function
        """
        cluster_id.TestingApi.enable_mock_id()
        self.assertTrue(cluster_id.is_valid(cluster_id.TestingApi.MOCK_ID))

        mock_id_upper = cluster_id.TestingApi.MOCK_ID.upper()
        self.assertEqual(cluster_id.parse(mock_id_upper), cluster_id.TestingApi.MOCK_ID)

    def test_disable_mock_id(self):
        """
        Test the disable_mock_id function
        """
        cluster_id.TestingApi.disable_mock_id()
        self.assertFalse(cluster_id.is_valid(cluster_id.TestingApi.MOCK_ID))

        mock_id_capitalized = cluster_id.TestingApi.MOCK_ID.capitalize()
        self.assertEqual(cluster_id.parse(mock_id_capitalized), None)

    def test_max_length(self):
        """
        Verify that the mock id fits within the maximum length.
        """
        cluster_id.TestingApi.enable_mock_id()
        self.assertTrue(len(cluster_id.TestingApi.MOCK_ID) <= cluster_id.MAX_LENGTH)

    def test_is_valid_with_all_known(self):
        """
        Test the is_valid function with each of the known id constants.
        """
        cluster_id.TestingApi.disable_mock_id()
        self.assertFalse(cluster_id.TestingApi.MOCK_ID in cluster_id.ALL_KNOWN)
        count_without_mock = len(cluster_id.ALL_KNOWN)

        cluster_id.TestingApi.enable_mock_id()
        self.assertEqual(len(cluster_id.ALL_KNOWN), count_without_mock + 1)
        self.assertTrue(cluster_id.TestingApi.MOCK_ID in cluster_id.ALL_KNOWN)

        for id_ in cluster_id.ALL_KNOWN:
            self.assertTrue(cluster_id.is_valid(id_))
