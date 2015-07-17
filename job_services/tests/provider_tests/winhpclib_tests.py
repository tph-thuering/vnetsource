from django.test import TestCase
from ...providers.winhpc.third_party.winhpclib import Error


class ErrorTests(TestCase):
    """
    Tests for the Error class in winhpclib.
    """
    def test_init(self):
        status = "Error status"
        reason = "Error reason"
        details = "Error details"
        error = Error(status, reason, details)
        self.assertEqual(error.status, status)
        self.assertEqual(error.reason, reason)
        self.assertEqual(error.details, details)

    def test_error_class_str_representation_with_details(self):
        status = "Error status"
        reason = "Error reason"
        details = "Error details"
        error = Error(status, reason, details)
        self.assertEqual(error.__str__(), str(status)+" "+str(reason)+", \nDetails: "+str(details))
