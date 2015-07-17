from django.test import TestCase
from ..api import Status


class APITests(TestCase):
    """
    Unit tests for the api classes.
    """
    def test_status_verify_attributes(self):
        """
        Tests for the Status verify_attributes method.
        """
        # parameters must be integers
        self.assertRaises(TypeError, Status, "a", 1, 1)
        self.assertRaises(TypeError, Status, 1, "a", 1)
        self.assertRaises(TypeError, Status, 1, 1, "a")
        # n_replications must be > 0
        self.assertRaises(ValueError, Status, 0, 0, 0)
        # completed_replications and failed_replications must be > -1
        self.assertRaises(ValueError, Status, 1, -1, 1)
        self.assertRaises(ValueError, Status, 1, 1, -1)
        # completed_replications + failed_replications must be < n_replications
        self.assertRaises(ValueError, Status, 1, 1, 1)
        # completed_replications and failed_replications must be < n_replications
        self.assertRaises(ValueError, Status, 1, 2, 1)
        self.assertRaises(ValueError, Status, 1, 1, 2)

    def test_status_percent_completed(self):
        """
        Tests for the Status percent_completed method.
        """
        self.status = Status(100, 50, 30)
        self.verify_status_attributes()
        self.assertEqual(self.status.percent_completed(), 50.0)

    def test_status_percent_running(self):
        """
        Tests for the Status percent_running method.
        """
        self.status = Status(100, 50, 30)
        self.verify_status_attributes()
        self.assertEqual(self.status.percent_running(), 20.0)

    def test_status_percent_failed(self):
        """
        Tests for the Status percent_failed method.
        """
        self.status = Status(100, 50, 30)
        self.verify_status_attributes()
        self.assertEqual(self.status.percent_failed(), 30.0)

    def verify_status_attributes(self):
        """
        Test the the attributes were set properly.
        """
        self.assertEqual(self.status.n_replications, 100)
        self.assertEqual(self.status.completed_replications, 50)
        self.assertEqual(self.status.failed_replications, 30)
        self.assertEqual(self.status.running_replications, 20)