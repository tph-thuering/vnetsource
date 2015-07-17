"""
This module is responsible for dispatching requests that come in from the package's API to the appropriate
service providers.

.. include:: ../docs/django-links.rst
"""
import datetime
import logging

from . import conf, cluster_id, dispatcher_conf
from .api import ApiErrors
from .providers import factories
from .models import RunProvider, SubmittedJobs
from .util import validate_run_param, validate_user_param, has_been_submitted


conf.configure_component()


def get_status(run, user):
    """
    Get the status of a run (may be an estimate).

    :param run: The model run to get the status for.  If the parameter is an integer, then it is the model run's
                primary key.
    :type  run: :py:class:`~data_services.models.DimRun` or int

    :param user: The person requesting the status of the model run.
    :type  user: User_

    :returns: A :py:class:`~job_services.api.Status` object.

    :raises: **AssertionError** - if there's an error with the parameters (see note below).

    Note: When this function raises an AssertionError, the exception's first argument is one of these constants:
      * :py:class:`~job_services.api.ApiErrors`.RUN_NOT_SUBMITTED
      * :py:class:`~job_services.api.ApiErrors`.RUN_PARAM_BAD_ID
      * :py:class:`~job_services.api.ApiErrors`.RUN_PARAM_BAD_TYPE
      * :py:class:`~job_services.api.ApiErrors`.USER_PARAM_BAD_TYPE
    """
    # validate parameters
    run_obj = validate_run_param(run)
    validate_user_param(user)
    assert has_been_submitted(run_obj), ApiErrors.RUN_NOT_SUBMITTED

    provider_name = RunProvider.objects.get(run=run_obj).provider
    provider_factory = factories.get_factory(provider_name)
    try:
        assert provider_factory is not None
    except AssertionError:
        logger = logging.getLogger(__name__)
        logger.exception('no factory for provider "%s", which is associated with run %d' % (provider_name, run_obj.id))
        raise

    provider = provider_factory.create_provider(run_obj, user)
    assert provider is not None
    return provider.get_run_status()


# Default algorithm for selecting a provider for submitting a run
DEFAULT_SELECTION_ALGORITHM = dispatcher_conf.selection_algorithm

# The algorithm actually called by the "submit" function
_selection_algorithm = DEFAULT_SELECTION_ALGORITHM


def submit(run, user, cluster=cluster_id.AUTO, **aux_submit_params):
    """
    Submits a model run to a computing cluster for execution.

    :param run: The model run to be submitted to a cluster for execution.  If the parameter is an integer, then it is
                the model run's primary key.
    :type  run: :py:class:`~data_services.models.DimRun` or int

    :param user: The person submitting the run.
    :type  user: User_

    :param cluster: The cluster to submit the model run to.  Must be one of the constants defined in :ref:`cluster-IDs`.
                    If not specified, then the cluster is automatically selected.
    :type  cluster: str

    :param aux_submit_params: Additional parameters for submit. These parameters are expected to be deprecated in
                              future versions. Currently reps_per_exec and manifest are pulled from this dictionary.
    :type  aux_submit_params: dict

    :raises AssertionError: if there's an error with the parameters (see note below).
    :raises RuntimeError:   if there's an error with submitting the simulation to the cluster (e.g., connectivity
                            problems).

    Note: When this function raises an AssertionError, the exception's first argument is one of these constants:
      * :py:class:`~job_services.api.ApiErrors`.CLUSTER_PARAM_BAD_ID
      * :py:class:`~job_services.api.ApiErrors`.CLUSTER_PARAM_BAD_TYPE
      * :py:class:`~job_services.api.ApiErrors`.RUN_ALREADY_SUBMITTED
      * :py:class:`~job_services.api.ApiErrors`.RUN_PARAM_BAD_ID
      * :py:class:`~job_services.api.ApiErrors`.RUN_PARAM_BAD_TYPE
      * :py:class:`~job_services.api.ApiErrors`.USER_PARAM_BAD_TYPE
    """
    reps_per_exec = aux_submit_params.get('reps_per_exec', 1)
    manifest = aux_submit_params.get('manifest', False)

    run_obj = validate_run_param(run)
    assert not has_been_submitted(run), ApiErrors.RUN_ALREADY_SUBMITTED

    validate_user_param(user)
    try:
        assert cluster_id.is_valid(cluster), ApiErrors.CLUSTER_PARAM_BAD_ID
    except TypeError:
        raise AssertionError(ApiErrors.CLUSTER_PARAM_BAD_TYPE)

    p, provider_message = _selection_algorithm(run_obj, user, cluster, manifest)
    if p is None:
        raise RuntimeError(provider_message)
    success = p.submit_jobs(reps_per_exec=reps_per_exec)
    if success:
        SubmittedJobs.objects.create(user=user,
                                     cluster=p.cluster,
                                     number_of_jobs=run_obj.numjobs(),
                                     date=datetime.date.today())
        RunProvider.objects.get_or_create(run=run_obj, provider=p.name)
        #TODO Should we actually return the cluster name for when it's selected automatically?
        return
    raise RuntimeError('submission to cluster "%s" failed', p.cluster.id)


class TestingApi(object):
    """
    API for unit tests.
    """
    @staticmethod
    def set_selection_algorithm(selector):
        """
        Set the algorithm (i.e., callable object) that's used to select a provider.
        """
        assert callable(selector)
        global _selection_algorithm
        _selection_algorithm = selector