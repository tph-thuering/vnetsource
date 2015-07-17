"""
Various helper constants and functions.
"""
from django.contrib.auth.models import User

from data_services.adapters import EMOD_Adapter, OM_Adapter
from data_services.models import DimRun
from simulation_models import model_id

from .api import ApiErrors
from .models import RunProvider

EMOD_ID = EMOD_Adapter.model_id
OPEN_MALARIA_ID = OM_Adapter.model_id


_id_mapping = {
    EMOD_ID: model_id.EMOD,
    OPEN_MALARIA_ID: model_id.OPEN_MALARIA,
}


def get_model_id(run):
    """
    Get the model id for a run.

    :param DimRun run: The model run
    :returns str: An id constant defined in simulation_models.model_id or None
    """
    return _id_mapping.get(run.models_key_id, None)


def validate_run_param(run):
    """
    Validates the run parameter for API functions.

    :param run: The model run parameter to be validated.  If parameter is an integer, then it is the
                run's primary key.
    :type  run: :py:class:`~data_services.models.DimRun` or int

    :returns: A :py:class:`~data_services.models.DimRun` instance

    :raises AssertionError: If the wrong data type was passed in for the parameter, then the exception's first argument
                            is ApiErrors.RUN_PARAM_BAD_TYPE.  If the parameter is an unknown primary key, then the
                            exception's first argument is ApiErrors.RUN_PARAM_BAD_ID.
    """
    if isinstance(run, DimRun):
        return run
    assert isinstance(run, int), ApiErrors.RUN_PARAM_BAD_TYPE
    try:
        return DimRun.objects.get(id=run)
    except DimRun.DoesNotExist:
        raise AssertionError(ApiErrors.RUN_PARAM_BAD_ID)


def validate_user_param(user):
    """
    Validates the user parameter for API functions.

    :param user: The parameter to be validated.
    :type  user: User_

    :raises AssertionError: if the wrong data type was passed in for a parameter.  The exception's first argument is
    ApiErrors.USER_PARAM_BAD_TYPE.
    """
    assert isinstance(user, User), ApiErrors.USER_PARAM_BAD_TYPE


def has_been_submitted(run):
    """
    Determines whether or not the run has been submitted.
    :param run: A DimRUn instance.
    :return: True or False
    """
    tmp_run = validate_run_param(run)
    return RunProvider.objects.filter(run=tmp_run).exists()
