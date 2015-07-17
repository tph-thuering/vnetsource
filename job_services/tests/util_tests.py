from django.test import TestCase

from lib.error_mixins import CallerErrorMixin

from .data_mixins import SetupRunMixin
from .. import util
from ..api import ApiErrors
from ..models import RunProvider


class UtilTests(SetupRunMixin, CallerErrorMixin, TestCase):
    """
    Unit tests for the util module.
    """
    @classmethod
    def setUpClass(cls):
        cls.bad_run_id = 9999

    def setUp(self):
        """
        Create a run for use in the tests.
        """
        self.setup_run()

    def test_validate_run_param(self):
        """
        Test the validate_run_param function with good data.
        """
        self.assertEqual(util.validate_run_param(self.run), self.run)
        self.assertEqual(util.validate_run_param(self.run.id), self.run)

    def test_validate_run_param_with_bad_type(self):
        """
        Test the validate_run_param function with parameters of the wrong type.
        """
        self.assertCallerError(ApiErrors.RUN_PARAM_BAD_TYPE, util.validate_run_param, {})
        self.assertCallerError(ApiErrors.RUN_PARAM_BAD_TYPE, util.validate_run_param, [])
        self.assertCallerError(ApiErrors.RUN_PARAM_BAD_TYPE, util.validate_run_param, ())
        self.assertCallerError(ApiErrors.RUN_PARAM_BAD_TYPE, util.validate_run_param, "HI")

    def test_validate_run_param_with_bad_id(self):
        """
        Test the validate_run_param function with a bad run id.
        """
        self.assertCallerError(ApiErrors.RUN_PARAM_BAD_ID, util.validate_run_param, self.bad_run_id)

    def test_validate_user_param(self):
        """
        Test the validate_user_param function with good data.
        """
        try:
            util.validate_user_param(self.user)
        except Exception, exc:
            self.fail('Expected no exceptions, but this exception was raised: %s' % repr(exc))

    def test_validate_user_param_with_bad_type(self):
        """
        Test the validate_user_param function with parameters that are the wrong type.
        """
        self.assertCallerError(ApiErrors.USER_PARAM_BAD_TYPE, util.validate_user_param, 1)
        self.assertCallerError(ApiErrors.USER_PARAM_BAD_TYPE, util.validate_user_param, {})
        self.assertCallerError(ApiErrors.USER_PARAM_BAD_TYPE, util.validate_user_param, [])
        self.assertCallerError(ApiErrors.USER_PARAM_BAD_TYPE, util.validate_user_param, ())
        self.assertCallerError(ApiErrors.USER_PARAM_BAD_TYPE, util.validate_user_param, "HI")

    def test_has_been_submitted(self):
        """
        """
        RunProvider.objects.all().delete()
        self.assertEqual(util.has_been_submitted(self.run), False)
        RunProvider.objects.create(run=self.run, provider="mock")
        self.assertEqual(util.has_been_submitted(self.run), True)