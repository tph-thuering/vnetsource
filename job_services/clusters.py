"""
Computing clusters
"""

from . import cluster_id
from .conf_err import ConfigurationError
import conf_err


# Configured clusters (key = cluster id, value = Cluster instance)
_clusters = dict()


class Cluster(object):
    """
    A computing cluster where model simulations are executed.
    """
    def __init__(self, id_, description, password, server, username):
        self.id = id_
        self.description = description
        self.password = password
        self.server = server
        self.username = username

    def __str__(self):
        return self.id


def get(id_):
    """
    Get a cluster object by its id.

    :param id_: The id of the cluster to fetch.
    :type  id_: str

    :returns: A :py:class:`~job_services.clusters.Cluster` object or None if the id_ is valid but that cluster was not
              configured in the settings.

    :raises TypeError: if id_ is not a string or unicode
    :raises ValueError: if id_ is not a known ID constant
    """
    if not cluster_id.is_valid(id_):
        raise ValueError('Invalid cluster id: "%s"' % id_)
    try:
        return _clusters[id_]
    except KeyError:
        return None


class TestingApi(object):
    """
    API for unit tests to create a mock cluster.
    """
    MOCK_CLUSTER_ID = cluster_id.TestingApi.MOCK_ID
    @staticmethod
    def enable_mock_cluster():
        """
        Enable the mock cluster.
        """
        cluster_id.TestingApi.enable_mock_id()
        _clusters[TestingApi.MOCK_CLUSTER_ID] = Cluster(TestingApi.MOCK_CLUSTER_ID, "mock cluster", "mock", "mock",
                                                        "mock")

    @staticmethod
    def disable_mock_cluster():
        """
        Disable the mock cluster.
        """
        cluster_id.TestingApi.disable_mock_id()
        del(_clusters[TestingApi.MOCK_CLUSTER_ID])

    @staticmethod
    def add_cluster(id, description="", password="", server="", username=""):
        assert cluster_id.is_valid(id)
        _clusters[id] = Cluster(id, description, password, server, username)


class ConfigurationErrorCodes(object):
    BAD_ID = 'bad id'
    DEFINITION_TYPE = 'definition: wrong type'
    DESCRIPTION_TYPE = 'description: wrong type'
    PASSWORD_TYPE = "password: wrong type"
    SERVER_TYPE = "server: wrong type"
    USERNAME_TYPE = "username: wrong type"
    NO_DEFINITIONS = 'no definitions'
    NO_DESCRIPTION = 'description: missing'
    NO_PASSWORD = "password: missing"
    NO_SERVER = "server: missing"
    NO_USERNAME = "username: missing"


def initialize(settings):
    """
    Initialize the module by loading cluster configuration settings.  The clusters are defined in a dictionary like
    this:

        {
            cluster_id.PSC_LINUX : {
                'description' : 'Linux cluster at Pittsburgh Supercomputing Center',
            },
            cluster_id.PSC_WINDOWS : {
                'description' : 'Windows cluster at Pittsburgh Supercomputing Center',
            },
        }
    """
    if not isinstance(settings, dict):
        raise ConfigurationError('expected dictionary', conf_err.ConfigurationErrorCodes.SETTINGS_TYPE)

    for (id_, definition) in settings.iteritems():
        try:
            valid_id = cluster_id.is_valid(id_)
        except TypeError:
            valid_id = False
        if not valid_id:
            raise ConfigurationError('invalid cluster id: "%s"' % id_, ConfigurationErrorCodes.BAD_ID)
        if not isinstance(definition, dict):
            raise ConfigurationError('definition for cluster "%s" is a not dictionary' % id_,
                                     ConfigurationErrorCodes.DEFINITION_TYPE)
        if 'description' not in definition:
            raise ConfigurationError('no description for cluster "%s"' % id_, ConfigurationErrorCodes.NO_DESCRIPTION)
        description = definition['description']
        if not isinstance(description, basestring):
            raise ConfigurationError('description for cluster "%s" is not a string' % id_,
                                     ConfigurationErrorCodes.DESCRIPTION_TYPE)

        if 'password' not in definition:
            raise ConfigurationError('no password for cluster "%s"' % id_, ConfigurationErrorCodes.NO_PASSWORD)
        password = definition['password']
        if not isinstance(password, basestring):
            raise ConfigurationError('password for cluster "%s" is not a string' % id_,
                                     ConfigurationErrorCodes.PASSWORD_TYPE)

        if 'server' not in definition:
            raise ConfigurationError('no server for cluster "%s"' % id_, ConfigurationErrorCodes.NO_SERVER)
        server = definition['server']
        if not isinstance(server, basestring):
            raise ConfigurationError('server for cluster "%s" is not a string' % id_,
                                     ConfigurationErrorCodes.SERVER_TYPE)

        if 'username' not in definition:
            raise ConfigurationError('no username for cluster "%s"' % id_, ConfigurationErrorCodes.NO_USERNAME)
        username = definition['username']
        if not isinstance(username, basestring):
            raise ConfigurationError('username for cluster "%s" is not a string' % id_,
                                     ConfigurationErrorCodes.USERNAME_TYPE)

        # Note: other keys are ignored
        _clusters[id_] = Cluster(id_, description, password, server, username)

    if len(_clusters.keys()) == 0:
        raise ConfigurationError('At least one cluster must be configured', ConfigurationErrorCodes.NO_DEFINITIONS)


def delete_all():
    """
    Delete all the cluster definitions.  Used for tear down in unit tests.
    """
    global _clusters
    _clusters = dict()