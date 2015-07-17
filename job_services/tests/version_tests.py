from django.test import TestCase
from .. import version


class VersionTests(TestCase):
    """
    Tests for the version module.
    """
    def test_version_comparison(self):
        v1 = version.Version(1, 0)
        v2 = version.Version(2, 0)
        v3 = version.Version(1, 1)
        v4 = version.Version(2, 0)
        # compare version 1 and 2
        self.assertTrue(v2 > v1)
        self.assertFalse(v2 < v1)
        self.assertTrue(v1 < v2)
        self.assertFalse(v1 > v2)
        self.assertFalse(v2 == v1)
        # compare version 1 and 3
        self.assertTrue(v3 > v1)
        self.assertFalse(v3 < v1)
        self.assertTrue(v1 < v3)
        self.assertFalse(v1 > v3)
        self.assertFalse(v3 == v1)
        # compare version 1 and 4
        self.assertTrue(v4 > v1)
        self.assertFalse(v4 < v1)
        self.assertTrue(v1 < v4)
        self.assertFalse(v1 > v4)
        self.assertFalse(v4 == v1)
        # compare version 2 and 3
        self.assertTrue(v2 > v3)
        self.assertFalse(v2 < v3)
        self.assertTrue(v3 < v2)
        self.assertFalse(v3 > v2)
        self.assertFalse(v2 == v3)
        # compare version 2 and 4
        self.assertFalse(v2 > v4)
        self.assertFalse(v2 < v4)
        self.assertFalse(v4 < v2)
        self.assertFalse(v4 > v2)
        self.assertTrue(v2 == v4)
        # compare version 3 and 4
        self.assertFalse(v3 > v4)
        self.assertTrue(v3 < v4)
        self.assertFalse(v4 < v3)
        self.assertTrue(v4 > v3)
        self.assertFalse(v3 == v4)

    def test_version_string(self):
        v = version.Version(1, 2)
        self.assertEqual(v.__str__(), "1.2")

    def test_version_init(self):
        v = version.Version(1, 2)
        self.assertEqual(v.major, 1)
        self.assertEqual(v.minor, 2)
