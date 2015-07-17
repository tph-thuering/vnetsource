from abc import ABCMeta, abstractmethod
from data_services.models import DimRun
from django.contrib.auth.models import User
from .definitions import ProviderDefinition


class ProviderBase(ProviderDefinition):
    """
    Defines the provider API. All provider implementations should inherit from this class and should define the methods
    here based on the particulars of the cluster and/or simulation model the provider is for.

    .. py:attribute:: run

       The run this provider is being used for.  *(DimRun*

    .. py:attribute:: user

       The Django User this provider is being used for.  *(User)*
    """
    __metaclass__ = ABCMeta

    def __init__(self, definition, run, user):
        super(ProviderBase, self).__init__(definition.name, definition.cluster, definition.simulation_model,
                                           definition.aux_params)
        assert isinstance(run, DimRun)
        assert isinstance(user, User)
        self.run = run
        self.user = user

    @abstractmethod
    def get_run_status(self):
        """
        Returns a status object containing information about the run.
        """
        raise NotImplementedError # pragma: no cover

    @abstractmethod
    def submit_jobs(self, reps_per_exec):
        """
        Submits the jobs for the associated model run to the cluster for execution.
        """
        raise NotImplementedError # pragma: no cover
