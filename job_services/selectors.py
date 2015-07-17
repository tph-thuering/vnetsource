from simulation_models import model_id
from .quotas import exceeds_quota
from .util import get_model_id
from .providers import factories, provider_name
from . import cluster_id, clusters


OM_SUBMISSION_NOT_SUPPORTED = "Open Malaria job submission is not supported in this version."
SUCCESS_MESSAGE = "Success"
NO_PROVIDERS_FOUND = "No available providers were found for cluster %s"


def select_provider(run, user, cluster, manifest=False):
    """
    Returns a provider for the given run and user. This is meant to be used for unsubmitted runs.

    :param run: A DimRun object to obtain a provider for.
    :type  run: :py:class:`~data_services.models.DimRun`
    :param user: A Django User to obtain a provider for.
    :type user: User_
    :param cluster: The cluster to submit the job to. If not specified, cluster is chosen for the user.
    :type cluster: str
    :param manifest: Whether or not to use manifest job submission.
    :type manifest: bool
    :returns: A provider instance.
    """
    # currently only EMOD is supported by job services
    #TODO add OpenMalaria support
    if get_model_id(run) == model_id.OPEN_MALARIA:
        return None, OM_SUBMISSION_NOT_SUPPORTED

    # determine the ideal cluster to submit jobs to
    cluster_obj, message = select_cluster_for_run(run, user, cluster)
    if cluster_obj is None:
        return cluster_obj, message

    # get provider factory based on the cluster
    provider_factory, message = select_provider_factory(cluster_obj, manifest)
    if provider_factory is None:
        return None, message
    provider = provider_factory.create_provider(run, user)
    return provider, message


def select_cluster_for_run(run, user, cluster):
    """
    Based on the run and user, determine the ideal cluster to submit jobs to.
    :param run: A DimRun object.
    :param user: A Django User.
    :param cluster: The name of a cluster that the user has specified. If not specified, the cluster is chosen for
    the user.
    :return: A cluster object or None and a message, as a tuple.
    """
    if cluster == cluster_id.AUTO:
        # currently only one valid cluster exists. Later this function will check quotas, permissions, load balancing,
        # and other metrics to determine the best available cluster, if an available cluster exists
        # TODO update the settings file and this method to reflect the move to Notre Dame
        cluster_name = cluster_id.ND_WINDOWS
    else:
        # user has specified which cluster they wish to submit jobs to. Determine if its a valid choice.
        # may need to check things such as manifest support and permissions
        cluster_name = cluster

    cluster_obj = clusters.get(cluster_name)
    #TODO determine what kind of error to raise here
    assert cluster_obj is not None

    exceeds, exceeds_message = exceeds_quota(run, user, cluster_obj)
    if exceeds:
        return None, exceeds_message

    return cluster_obj, SUCCESS_MESSAGE


def _get_providers_for_cluster(cluster_obj):
    """
    Determine which providers are associated with the specified cluster. This method assumes the job_services settings
    have been properly configured. It is an internal function and functionality is tested only for internal use.
    :param cluster_obj: A cluster object to find providers for.
    :return: A list of provider names.
    """
    return [name for name, factory in factories._factories.iteritems()
            if str(factory.provider_definition.cluster) == str(cluster_obj.id)]


def select_provider_factory(cluster_obj, manifest):
    """
    Returns a provider class which is used to submit jobs. The provider is chosen based on the simulation type
    (EMOD, OpenMalaria, etc.), the number of jobs currently running on clusters suited to run that simulation model,
    and the user's credentials and quotas. This is meant to be used for runs that have not been submitted.

    :param cluster_obj: The cluster to submit the job to. If not specified, cluster is chosen for the user.
    :type cluster_obj: :py:class:`~job_services.clusters.Cluster`
    :param manifest: Whether or not to use manifest job submission.
    :type manifest: bool
    :returns: A tuple containing a provider and a key, or none and an error message.
    """
    if manifest:
        name = provider_name.MANIFEST_PROTOTYPE
    else:
        raise RuntimeError("Non-manifest provider has been discontinued") #name = provider_name.PROTOTYPE

    if name not in _get_providers_for_cluster(cluster_obj):
        return None, NO_PROVIDERS_FOUND % cluster_obj.id

    factory = factories.get_factory(name)
    return factory, name