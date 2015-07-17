import mock
from unittest import TestCase
from django.test.utils import override_settings
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from .. import conf
from .cluster_tests import ClusterTesterMixin

# Example Start (included in Sphinx-generated documentation; see conf.rst)
from job_services import cluster_id, dispatcher_conf
from job_services.providers import provider_name
from simulation_models import model_id
from ..providers.conf import parse_callable
from ..conf_err import ConfigurationError, ConfigurationErrorCodes

try:
    from . import secrets
except ImportError:
    from . import secrets_default as secrets


JOB_SERVICES = {
    'default quotas': {
        'max per run': 10,
        'max per month': 1000,
    },
    'clusters': {
        cluster_id.PSC_LINUX: {
            'description': 'Linux cluster at Pittsburgh Supercomputer Center',
            'server': secrets.PscLinux.SERVER,
            'username': secrets.PscLinux.USERNAME,
            'password': secrets.PscLinux.PASSWORD
        },
        cluster_id.ND_WINDOWS: {
            'description': 'Windows cluster at Notre Dame',
            'server': secrets.NotreDameWindows.SERVER,
            'username': secrets.NotreDameWindows.USERNAME,
            'password': secrets.NotreDameWindows.PASSWORD
        },
    },
    'providers': (
        {
            'name': provider_name.MANIFEST_PROTOTYPE,
            'cluster': cluster_id.ND_WINDOWS,
            'class': 'job_services.providers.winhpc.WinHpcManifestProvider.WinHpcManifestProvider',
            "model": model_id.EMOD,
        },
    ),
    "dispatcher": {
       "provider selector": 'job_services.experimental.dispatcher.experimental_select_provider',
    },
}
# Example End


def copy_dict_without_key(dictionary, key_to_skip):
    """
    Copy a dictionary but skip a particular key.  Used to duplicate JOB_SERVICES settings without a particular key.
    """
    result = dict()
    for k, v in dictionary.iteritems():
        if k != key_to_skip:
            result[k] = v
    return result


class ConfigurationTests(ClusterTesterMixin, TestCase):
    """
    Unit tests for overall configuration.
    """

    def tearDown(self):
        """
        Reset all the component settings.
        """
        conf.reset_settings()

    def assertRaisesMissingKeyError(self, expected_key, callable_obj, *args):
        """
        Assert that a callable raises a MissingKeyError for a particular key.
        """
        try:
            callable_obj(*args)
            self.fail('MissingKeyError, but no exception raised')
        except conf.MissingKeyError, exc:
            self.assertEqual(exc.key, expected_key)
        except Exception, exc:
            self.fail('Expected MissingKeyError, but got %s' % repr(exc))

    def assert2ClustersExist(self):
        """
        Assert that the 2 known clusters have been defined
        """
        get_cluster_description = lambda id_: JOB_SERVICES['clusters'][id_]['description']
        self.assertClusterExists(cluster_id.PSC_LINUX, get_cluster_description(cluster_id.PSC_LINUX))
        self.assertClusterExists(cluster_id.ND_WINDOWS, get_cluster_description(cluster_id.ND_WINDOWS))

    def test_load_settings_with_no_job_services_setting(self):
        del settings.JOB_SERVICES
        self.assertRaises(ImproperlyConfigured, conf.load_settings)

    @override_settings(JOB_SERVICES=JOB_SERVICES)
    def test_load_settings_with_example(self):
        """
        Test the load_settings function with a complete example of JOB_SERVICES setting.
        """
        conf.load_settings()
        self.assert2ClustersExist()

    def test_load_settings_with_actual(self):
        """
        Test the load_settings function with the actual JOB_SERVICES setting.
        """
        conf.load_settings()
        get_cluster_description = lambda id_: JOB_SERVICES['clusters'][id_]['description']
        self.assertClusterExists(cluster_id.ND_WINDOWS, get_cluster_description(cluster_id.ND_WINDOWS))

    @override_settings(JOB_SERVICES=copy_dict_without_key(JOB_SERVICES, conf.Keys.DEFAULT_QUOTAS))
    def test_load_settings_without_quotas(self):
        """
        Test the load_settings function with a missing DEFAULT_QUOTAS key.
        """
        self.assertRaisesMissingKeyError(conf.Keys.DEFAULT_QUOTAS, conf.load_settings)

    @override_settings(JOB_SERVICES=copy_dict_without_key(JOB_SERVICES, conf.Keys.CLUSTERS))
    def test_load_settings_without_clusters(self):
        """
        Test the load_settings function with a missing CLUSTERS key.
        """
        self.assertRaisesMissingKeyError(conf.Keys.CLUSTERS, conf.load_settings)

    @override_settings(JOB_SERVICES=copy_dict_without_key(JOB_SERVICES, conf.Keys.PROVIDERS))
    def test_load_settings_without_providers(self):
        """
        Test the load_settings function with a missing PROVIDERS key.
        """
        self.assertRaisesMissingKeyError(conf.Keys.PROVIDERS, conf.load_settings)

    @override_settings(JOB_SERVICES=copy_dict_without_key(JOB_SERVICES, conf.Keys.DISPATCHER))
    def test_load_settings_without_dispatcher(self):
        """
        Test the load_settings function with a missing DISPATCHER key.
        """
        conf.load_settings()
        self.assertEqual(dispatcher_conf.selection_algorithm,
                         parse_callable(JOB_SERVICES['dispatcher']['provider selector']))

    @mock.patch("job_services.conf.quotas.load_defaults")
    def test_load_settings_with_configuration_error_thrown(self, mock_load_defaults):
        mock_load_defaults.side_effect = ConfigurationError("test message")
        self.assertRaises(ConfigurationError, conf.load_settings)

    @mock.patch("job_services.conf.quotas.load_defaults")
    def test_load_settings_with_configuration_error_thrown_for_settings_type(self, mock_load_defaults):
        mock_load_defaults.side_effect = ConfigurationError("mock type",
                                                            error_code=ConfigurationErrorCodes.SETTINGS_TYPE)
        self.assertRaises(ConfigurationError, conf.load_settings)


class LoadComponentSettingsTests(TestCase):
    """
    Unit tests of the loading of the component (JOB_SERVICES) settings.
    """
    @mock.patch("job_services.conf.load_settings")
    @mock.patch("sys.argv", [])  # So there's no test argument
    def test_configure_component_when_not_running_tests(self, mock_load_settings):
        """
        Verify that the settings are loaded when tests are not running by patching sys.argv so that the function is
        fooled into thinking tests are not running.
        """
        conf.configure_component()
        self.assertTrue(mock_load_settings.called)

    @mock.patch("job_services.conf.load_settings")
    @mock.patch("sys.argv", [])  # So there's no test argument
    @mock.patch("docs.sphinx.is_running", True)
    def test_configure_component_when_generating_docs(self, mock_load_settings):
        """
        Test that settings are not loaded when Sphinx is running to generate documentation.
        """
        conf.configure_component()
        self.assertFalse(mock_load_settings.called)

    @mock.patch("job_services.conf.load_settings")
    @mock.patch("docs.sphinx.is_running", False)
    def test_configure_component_when_running_tests(self, mock_load_settings):
        """
        Test that settings are not loaded when tests are running.
        """
        conf.configure_component()
        self.assertFalse(mock_load_settings.called)