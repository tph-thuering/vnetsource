from ...api import Status
from ...providers.base import ProviderBase


class MockProvider(ProviderBase):
    """
    A mock provider for use in unit testing the job services api.
    """
    def __init__(self, definition, run, user):
        super(MockProvider, self).__init__(definition, run, user)

    def get_run_status(self):
        """
        Mock get_run-status method.
        """
        return Status(100, 50, 10)

    def submit_jobs(self, reps_per_exec):
        """
        Mock submit_jobs method.
        :returns: tuple containing true and a message
        """
        if reps_per_exec:
            return True
        return False