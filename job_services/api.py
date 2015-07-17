"""
Classes used in the component's API.
"""

from lib.errors import CallerError


class Status:
    """
    Status information about a model run submitted to a computing cluster for execution.

    .. py:attribute:: n_replications

       The total number of replications that the model run has.  *(int)*

    .. py:attribute:: completed_replications

       The number of replications that have completed for the run.  *(int)*

    .. py:attribute:: failed_replications

       The number of replications that have failed (did not complete) for the run.  *(int)*
    """
    def __init__(self, n_replications=0, completed_replications=0, failed_replications=0):
        """
        Initialize a new instance.
        """
        self.n_replications = n_replications
        self.completed_replications = completed_replications
        self.failed_replications = failed_replications
        # make sure variables were initialized properly
        self.verify_attributes()

    @property
    def running_replications(self):
        """
        Return the number of running replications, computed from the total, completed, and failed replications.
        """
        return self.n_replications - self.failed_replications - self.completed_replications

    def percent_completed(self):
        """
        Compute the percent of successfully completed replications, as an integer ranging from 0 to 100, using the
        total number of replications.

        :returns: int ranging from 0 to 100
        """
        return (float(self.completed_replications) / self.n_replications) * 100

    def percent_failed(self):
        """
        Compute the percent of failed replications, as an integer ranging from 0 to 100, using the total number of
        replications.

        :returns: int ranging from 0 to 100
        """
        return (float(self.failed_replications) / self.n_replications) * 100

    def percent_running(self):
        """
        Compute the percent of replications still running, as an integer ranging from 0 to 100, using the total number
        of total replications, the number of completed replications, and the number of failed replications..

        :returns: int ranging from 0 to 100
        """
        return 100 - self.percent_completed() - self.percent_failed()

    def verify_attributes(self):
        """
        Check that the init attributes have the proper types and values.
        """
        if not isinstance(self.n_replications, int):
            raise TypeError("n_replications must be an integer.")

        if not isinstance(self.completed_replications, int):
            raise TypeError("completed_replications must be an integer.")

        if not isinstance(self.failed_replications, int):
            raise TypeError("failed_replications must be an integer.")

        if self.n_replications < 1:
            raise ValueError("n_replications must be an integer greater than zero.")

        if self.completed_replications < 0 or self.completed_replications > self.n_replications:
            raise ValueError("completed_replications must be an integer greater than -1 and less than n_replications.")

        if self.failed_replications < 0 or self.failed_replications > self.n_replications:
            raise ValueError("failed_replications must be an integer greater than -1 and less than n_replications.")

        if self.failed_replications + self.completed_replications > self.n_replications:
            message = "The number of failed replications plus the number of completed replications must be less than " \
                      "or equal to the total number of replications."
            raise ValueError(message)


class ApiErrors(object):
    """
    Errors in using the component's API.  These constants are defined as immutable instances of
    :py:class:`lib.errors.CallerError`.

    .. autoattribute:: job_services.api.ApiErrors.CLUSTER_PARAM_BAD_ID
    .. autoattribute:: job_services.api.ApiErrors.CLUSTER_PARAM_BAD_TYPE
    .. autoattribute:: job_services.api.ApiErrors.RUN_ALREADY_SUBMITTED
    .. autoattribute:: job_services.api.ApiErrors.RUN_NOT_SUBMITTED
    .. autoattribute:: job_services.api.ApiErrors.RUN_PARAM_BAD_ID
    .. autoattribute:: job_services.api.ApiErrors.RUN_PARAM_BAD_TYPE
    .. autoattribute:: job_services.api.ApiErrors.USER_PARAM_BAD_TYPE
    """
    CLUSTER_PARAM_BAD_ID = CallerError('invalid cluster id')
    CLUSTER_PARAM_BAD_TYPE = CallerError('cluster parameter must be string')
    RUN_ALREADY_SUBMITTED = CallerError('run has already been submitted')
    RUN_NOT_SUBMITTED = CallerError('run has not been submitted')
    RUN_PARAM_BAD_ID = CallerError('invalid run id')
    RUN_PARAM_BAD_TYPE = CallerError('run parameter must be DimRun or int')
    USER_PARAM_BAD_TYPE = CallerError('user parameter must be Django User')
