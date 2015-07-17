"""
Quotas are used to limit the number of jobs a user can submit to a particular cluster on a per run and per month basis.

.. include:: /docs/django-links.rst
"""

import datetime
from . import conf_err
from .models import SubmittedJobs, Quota
from .conf_err import ConfigurationError

_max_per_run = None
_max_per_month = None


class ConfigurationErrorCodes(object):
    """
    Error codes for the quotas module.
    """
    MAX_PER_MONTH_EXISTS = 'max_per_month: not present'
    MAX_PER_MONTH_TYPE = 'max_per_month: wrong type'
    MAX_PER_RUN_EXISTS = 'max_per_run: not present'
    MAX_PER_RUN_TYPE = 'max_per_run: wrong type'


def load_defaults(settings):
    """
    Load the default job quotas from the project's settings.  The quotas are specified in a dictionary::

        {
            'max per run' : 100,
            'max per month' : 1000,
        }

    :param settings: The project settings for default quotas.
    :type  settings: dict
    """
    if not isinstance(settings, dict):
        raise ConfigurationError('expected dictionary', conf_err.ConfigurationErrorCodes.SETTINGS_TYPE)

    mpm = settings.get("max per month", None)
    if not mpm:
        raise ConfigurationError('max_per_month is required', ConfigurationErrorCodes.MAX_PER_MONTH_EXISTS)
    if not isinstance(mpm, int):
        raise ConfigurationError('max_per_month must be an integer', ConfigurationErrorCodes.MAX_PER_MONTH_TYPE)

    mpr = settings.get("max per run", None)
    if not mpr:
        raise ConfigurationError('max_per_run is required', ConfigurationErrorCodes.MAX_PER_RUN_EXISTS)
    if not isinstance(mpr, int):
        raise ConfigurationError('max_per_run must be an integer', ConfigurationErrorCodes.MAX_PER_RUN_TYPE)

    global _max_per_month
    global _max_per_run
    _max_per_month = mpm
    _max_per_run = mpr


def submitted_this_month(user, cluster, month):
    """
    Compute the number of jobs submitted this month for the user and cluster associated to this object.

    :param month: An integer representing a month.
    :type  month: int
    :param user: A Django User.
    :type user: User_
    :param cluster: The cluster to compute a quota for.
    :type cluster: str
    :returns: Integer
    """
    return sum(item.number_of_jobs for item in SubmittedJobs.objects.filter(user=user,
                                                                            cluster=cluster,
                                                                            date__month=month))


EXCEEDS_MONTHLY_QUOTA = "Submitting this many jobs will exceed the user's monthly quota."
EXCEEDS_RUN_QUOTA = "Number of jobs exceeds maximum number of jobs per run."
QUOTA_NOT_EXCEEDED = "Quota not exceeded."


def exceeds_quota(run, user, cluster):
    """
    Indicates whether or not the number of jobs created by the run will exceed the user's quota for the given cluster.

    :param run: A DimRun object.
    :type  run: :py:class:`~data_services.models.DimRun`
    :param user: A Django User.
    :type user: User_
    :param cluster: The cluster to submit the job to.
    :type cluster: str
    :returns: A tuple containing True or False and a message
    """
    try:
        quota = Quota.objects.get(user=user, cluster=cluster)
        max_per_run = quota.max_per_run
        max_per_month = quota.max_per_month
    except Quota.DoesNotExist:
        max_per_run = _max_per_run
        max_per_month = _max_per_month
    submitted = submitted_this_month(user=user, cluster=cluster, month=datetime.date.today().month)
    number_to_submit = run.numjobs()
    if number_to_submit > max_per_run:
        return True, EXCEEDS_RUN_QUOTA
    if submitted + number_to_submit > max_per_month:
        return True, EXCEEDS_MONTHLY_QUOTA
    return False, QUOTA_NOT_EXCEEDED