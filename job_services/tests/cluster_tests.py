import mock
from unittest import TestCase
from .conf_err_mixins import ConfigurationErrorMixin
from .. import cluster_id, clusters, conf_err
from ..clusters import ConfigurationErrorCodes

try:
    from . import secrets
except ImportError:
    from . import secrets_default as secrets

class ClusterTesterMixin(TestCase):
    """
    Mixin for test suites that will check if clusters exist.
    """

    def assertClusterExists(self, id_, description):
        """
        Assert that a cluster with the specified id and description exists.
        """
        cluster = clusters.get(id_)
        self.assertTrue(isinstance(cluster, clusters.Cluster))
        self.assertEqual(cluster.id, id_)
        self.assertEqual(cluster.description, description)


class ClusterTests(ClusterTesterMixin, ConfigurationErrorMixin, TestCase):
    """
    Unit tests for clusters module.
    """
    PSC_LINUX_DESCRIPTION = 'Test description for cluster_id.PSC_LINUX'
    ND_WINDOWS_DESCRIPTION = 'Test description for cluster_id.ND_WINDOWS'

    def tearDown(self):
        clusters.delete_all()

    def test_delete_all(self):
        self.assertEqual(clusters._clusters, dict())
        clusters.TestingApi.enable_mock_cluster()
        self.assertNotEqual(clusters._clusters, dict())
        clusters.delete_all()
        self.assertEqual(clusters._clusters, dict())

    @mock.patch("job_services.clusters.cluster_id.is_valid")
    def test_get_with_invalid_cluster_id(self, mock_is_valid):
        mock_is_valid.return_value = False
        self.assertRaises(ValueError, clusters.get, "foo")

    @mock.patch("job_services.clusters.cluster_id.is_valid")
    def test_get_with_unconfigured_id(self, mock_is_valid):
        mock_is_valid.return_value = True
        self.assertEqual(None, clusters.get("foo"))

    def test_initialize_with_1_cluster(self):
        """
        Test the initialize function with one cluster definition.
        """
        clusters.initialize(
            {
                cluster_id.PSC_LINUX:
                    {
                        'description': self.PSC_LINUX_DESCRIPTION,
                        'server': secrets.PscLinux.SERVER,
                        'username': secrets.PscLinux.USERNAME,
                        'password': secrets.PscLinux.PASSWORD
                    }
            })
        self.assertClusterExists(cluster_id.PSC_LINUX, self.PSC_LINUX_DESCRIPTION)

    def test_initialize_with_2_clusters(self):
        """
        Test the initialize function with two cluster definitions.
        """
        clusters.initialize(
            {
                cluster_id.PSC_LINUX:
                    {
                        'description': self.PSC_LINUX_DESCRIPTION,
                        'server': secrets.PscLinux.SERVER,
                        'username': secrets.PscLinux.USERNAME,
                        'password': secrets.PscLinux.PASSWORD
                    },
                cluster_id.ND_WINDOWS:
                    {
                        'description': self.ND_WINDOWS_DESCRIPTION,
                        'server': secrets.NotreDameWindows.SERVER,
                        'username': secrets.NotreDameWindows.USERNAME,
                        'password': secrets.NotreDameWindows.PASSWORD
                    }
            })
        self.assertClusterExists(cluster_id.PSC_LINUX, self.PSC_LINUX_DESCRIPTION)
        self.assertClusterExists(cluster_id.ND_WINDOWS, self.ND_WINDOWS_DESCRIPTION)

    def test_initialize_with_wrong_type(self):
        """
        Test the initialize function with a parameter of the wrong data type (not a dictionary).
        """
        self.assertRaisesConfError(conf_err.ConfigurationErrorCodes.SETTINGS_TYPE, clusters.initialize, None)
        self.assertRaisesConfError(conf_err.ConfigurationErrorCodes.SETTINGS_TYPE, clusters.initialize, -8)
        self.assertRaisesConfError(conf_err.ConfigurationErrorCodes.SETTINGS_TYPE, clusters.initialize, tuple())
        self.assertRaisesConfError(conf_err.ConfigurationErrorCodes.SETTINGS_TYPE, clusters.initialize, [1, 2, 3])
        self.assertRaisesConfError(conf_err.ConfigurationErrorCodes.SETTINGS_TYPE, clusters.initialize, "foo")

    def test_initialize_with_no_keys(self):
        """
        Test the initialize function with an empty dictionary.
        """
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_DEFINITIONS, clusters.initialize, dict())

    def test_initialize_with_bad_ids(self):
        """
        Test the initialize function with bad cluster ids.
        """
        self.assertRaisesConfError(ConfigurationErrorCodes.BAD_ID, clusters.initialize, {'foo': None})
        self.assertRaisesConfError(ConfigurationErrorCodes.BAD_ID, clusters.initialize, {'': None})
        self.assertRaisesConfError(ConfigurationErrorCodes.BAD_ID, clusters.initialize, {16: None})

        self.assertRaisesConfError(ConfigurationErrorCodes.BAD_ID, clusters.initialize,
                                   {
                                       cluster_id.PSC_LINUX:
                                           {
                                               'description': self.PSC_LINUX_DESCRIPTION,
                                               'server': secrets.PscLinux.SERVER,
                                               'username': secrets.PscLinux.USERNAME,
                                               'password': secrets.PscLinux.PASSWORD
                                           },
                                       'bad id': None,
                                   })

    def test_initialize_with_bad_definition_type(self):
        """
        Test the initialize function with cluster definitions that are not dictionaries.
        """
        self.assertRaisesConfError(ConfigurationErrorCodes.DEFINITION_TYPE, clusters.initialize,
                                   {cluster_id.PSC_LINUX: None})
        self.assertRaisesConfError(ConfigurationErrorCodes.DEFINITION_TYPE, clusters.initialize,
                                   {cluster_id.PSC_LINUX: 'foo bar'})
        self.assertRaisesConfError(ConfigurationErrorCodes.DEFINITION_TYPE, clusters.initialize,
                                   {cluster_id.PSC_LINUX: [0, 1]})

    def test_initialize_with_no_description(self):
        """
        Test the initialize function with cluster definitions that have no 'description' key.
        """
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_DESCRIPTION, clusters.initialize,
                                   {cluster_id.ND_WINDOWS: dict()})
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_DESCRIPTION, clusters.initialize,
                                   {cluster_id.ND_WINDOWS: dict(Description='')})
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_DESCRIPTION, clusters.initialize,
                                   {cluster_id.ND_WINDOWS: dict(foo='Hello', bar='World')})

    def test_initialize_with_bad_description_type(self):
        """
        Test the initialize function with cluster definitions whose 'description' keys have non-string values.
        """
        self.assertRaisesConfError(ConfigurationErrorCodes.DESCRIPTION_TYPE, clusters.initialize,
                                   {cluster_id.ND_WINDOWS: dict(description=None)})
        self.assertRaisesConfError(ConfigurationErrorCodes.DESCRIPTION_TYPE, clusters.initialize,
                                   {cluster_id.ND_WINDOWS: dict(description=0.007)})
        self.assertRaisesConfError(ConfigurationErrorCodes.DESCRIPTION_TYPE, clusters.initialize,
                                   {cluster_id.ND_WINDOWS: dict(description=[])})
        self.assertRaisesConfError(ConfigurationErrorCodes.DESCRIPTION_TYPE, clusters.initialize,
                                   {cluster_id.ND_WINDOWS: dict(description=object())})

    def test_initialize_with_no_password(self):
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_PASSWORD, clusters.initialize,
                                   {cluster_id.ND_WINDOWS: dict(description="")})
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_PASSWORD, clusters.initialize,
                                   {cluster_id.ND_WINDOWS: dict(description="", Password="")})
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_PASSWORD, clusters.initialize,
                                   {cluster_id.ND_WINDOWS: dict(description="", foo='Hello', bar='World')})

    def test_initialize_with_bad_password_type(self):
        self.assertRaisesConfError(ConfigurationErrorCodes.PASSWORD_TYPE, clusters.initialize,
                                   {cluster_id.ND_WINDOWS: dict(description="", password=None)})
        self.assertRaisesConfError(ConfigurationErrorCodes.PASSWORD_TYPE, clusters.initialize,
                                   {cluster_id.ND_WINDOWS: dict(description="", password=[])})
        self.assertRaisesConfError(ConfigurationErrorCodes.PASSWORD_TYPE, clusters.initialize,
                                   {cluster_id.ND_WINDOWS: dict(description="", password=1)})
        self.assertRaisesConfError(ConfigurationErrorCodes.PASSWORD_TYPE, clusters.initialize,
                                   {cluster_id.ND_WINDOWS: dict(description="", password=object())})

    def test_initialize_with_no_server(self):
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_SERVER, clusters.initialize,
                                   {cluster_id.ND_WINDOWS: dict(description="", password="")})
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_SERVER, clusters.initialize,
                                   {cluster_id.ND_WINDOWS: dict(description="", password="", Server="")})
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_SERVER, clusters.initialize,
                                   {cluster_id.ND_WINDOWS: dict(description="", password="", foo='Hello',
                                                                 bar='World')})

    def test_initialize_with_bad_server_type(self):
        self.assertRaisesConfError(ConfigurationErrorCodes.SERVER_TYPE, clusters.initialize,
                                   {cluster_id.ND_WINDOWS: dict(description="", password="", server=None)})
        self.assertRaisesConfError(ConfigurationErrorCodes.SERVER_TYPE, clusters.initialize,
                                   {cluster_id.ND_WINDOWS: dict(description="", password="", server=1)})
        self.assertRaisesConfError(ConfigurationErrorCodes.SERVER_TYPE, clusters.initialize,
                                   {cluster_id.ND_WINDOWS: dict(description="", password="", server=[])})
        self.assertRaisesConfError(ConfigurationErrorCodes.SERVER_TYPE, clusters.initialize,
                                   {cluster_id.ND_WINDOWS: dict(description="", password="", server=object())})

    def test_initialize_with_no_username(self):
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_USERNAME, clusters.initialize,
                                   {cluster_id.ND_WINDOWS: dict(description="", password="", server="")})
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_USERNAME, clusters.initialize,
                                   {cluster_id.ND_WINDOWS: dict(description="", password="", server="", User="")})
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_USERNAME, clusters.initialize,
                                   {cluster_id.ND_WINDOWS: dict(description="", password="", server="", foo='Hello',
                                                                 bar='World')})

    def test_initialize_with_bad_username_type(self):
        self.assertRaisesConfError(ConfigurationErrorCodes.USERNAME_TYPE, clusters.initialize,
                                   {cluster_id.ND_WINDOWS: dict(description="", password="", server="",
                                                                 username=None)})
        self.assertRaisesConfError(ConfigurationErrorCodes.USERNAME_TYPE, clusters.initialize,
                                   {cluster_id.ND_WINDOWS: dict(description="", password="", server="",
                                                                 username=0.007)})
        self.assertRaisesConfError(ConfigurationErrorCodes.USERNAME_TYPE, clusters.initialize,
                                   {cluster_id.ND_WINDOWS: dict(description="", password="", server="", username=[])})
        self.assertRaisesConfError(ConfigurationErrorCodes.USERNAME_TYPE, clusters.initialize,
                                   {cluster_id.ND_WINDOWS: dict(description="", password="", server="",
                                                                 username=object())})

