import mock

from unittest import TestCase
from ... import cluster_id, clusters
from ..conf_err_mixins import ConfigurationErrorMixin
from ... import conf_err
from ...providers import factories
from ...providers.conf import (ConfigurationErrorCodes, initialize_provider, initialize_providers, parse_class,
                               valid_python_identifier, get_optional_settings, REQUIRED_KEYS, parse_callable)
from ...providers.definitions import ProviderDefinition
from simulation_models import model_id


class ProvidersInitializationTests(ConfigurationErrorMixin, TestCase):
    """
    Unit tests for initializing all the providers.
    """

    def test_initialize_providers_with_bad_type(self):
        """
        Test the initialize_providers function with parameters that are not tuples.
        """
        self.assertRaisesConfError(conf_err.ConfigurationErrorCodes.SETTINGS_TYPE, initialize_providers, None)
        self.assertRaisesConfError(conf_err.ConfigurationErrorCodes.SETTINGS_TYPE, initialize_providers, 'foo')
        self.assertRaisesConfError(conf_err.ConfigurationErrorCodes.SETTINGS_TYPE, initialize_providers, 3.14)
        self.assertRaisesConfError(conf_err.ConfigurationErrorCodes.SETTINGS_TYPE, initialize_providers, object())
        self.assertRaisesConfError(conf_err.ConfigurationErrorCodes.SETTINGS_TYPE, initialize_providers, [-1, '', None])

    def test_initialize_providers_with_0_providers(self):
        """
        Test the initialize_providers function with parameters that are empty (i.e, no providers).
        """
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_PROVIDERS, initialize_providers, tuple())


class ProviderInitializationTests(ConfigurationErrorMixin, TestCase):
    """
    Unit tests for initializing a single provider.
    """
    def setUp(self):
        clusters.TestingApi.enable_mock_cluster()

    def tearDown(self):
        factories.unregister_all()
        clusters.TestingApi.disable_mock_cluster()

    def test_initialize_provider_with_bad_type(self):
        """
        Test the initialize_provider function with parameters that are not dictionaries.
        """
        self.assertRaisesConfError(ConfigurationErrorCodes.NOT_DICTIONARY, initialize_provider, None)
        self.assertRaisesConfError(ConfigurationErrorCodes.NOT_DICTIONARY, initialize_provider, 'foo')
        self.assertRaisesConfError(ConfigurationErrorCodes.NOT_DICTIONARY, initialize_provider, 3.14)
        self.assertRaisesConfError(ConfigurationErrorCodes.NOT_DICTIONARY, initialize_provider, object())
        self.assertRaisesConfError(ConfigurationErrorCodes.NOT_DICTIONARY, initialize_provider, [-1, '', None])

    def test_initialize_provider_with_no_name(self):
        """
        Test the initialize_provider function with settings parameters that have no "name" key.
        """
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_NAME_KEY, initialize_provider, {})
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_NAME_KEY, initialize_provider, {'Name': 'foo'})
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_NAME_KEY, initialize_provider, {'name ': 'foo'})

    def test_initialize_provider_with_nonstring_name(self):
        """
        Test the initialize_provider function with settings parameters where the "name" key has non-string value.
        """
        self.assertRaisesConfError(ConfigurationErrorCodes.NAME_NOT_STRING, initialize_provider, {'name': None})
        self.assertRaisesConfError(ConfigurationErrorCodes.NAME_NOT_STRING, initialize_provider, {'name': -1})
        self.assertRaisesConfError(ConfigurationErrorCodes.NAME_NOT_STRING, initialize_provider, {'name': dict()})

    def test_initialize_provider_with_duplicate_name(self):
        """
        Test the initialize_provider function with settings parameters where the "name" key has non-string value.
        """
        cluster_id.TestingApi.enable_mock_id()
        provider_definition = ProviderDefinition('Foo Provider', clusters.get(clusters.TestingApi.MOCK_CLUSTER_ID),
                                                 'Foo Model')
        provider_factory = factories.Factory(object(), provider_definition)
        factories.register(provider_factory)
        self.assertRaisesConfError(ConfigurationErrorCodes.DUPLICATE_NAME, initialize_provider,
                                   {'name': provider_definition.name})
        cluster_id.TestingApi.disable_mock_id()

    def test_initialize_provider_with_no_cluster(self):
        """
        Test the initialize_provider function with settings parameters that have no "cluster" key.
        """
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_CLUSTER_KEY, initialize_provider, {'name': 'foo'})
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_CLUSTER_KEY, initialize_provider, {'name': 'foo',
                                                                                                 'CLUSTER': 'bar'})
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_CLUSTER_KEY, initialize_provider, {'name': 'foo',
                                                                                                 ' cluster': 'bar'})

    def test_initialize_provider_with_nonstring_cluster(self):
        """
        Test the initialize_provider function with settings parameters where the "cluster" key has non-string value.
        """
        self.assertRaisesConfError(ConfigurationErrorCodes.CLUSTER_NOT_STRING, initialize_provider, {'name': 'foo',
                                                                                                     'cluster': None})
        self.assertRaisesConfError(ConfigurationErrorCodes.CLUSTER_NOT_STRING, initialize_provider, {'name': 'foo',
                                                                                                     'cluster': -1})
        self.assertRaisesConfError(ConfigurationErrorCodes.CLUSTER_NOT_STRING, initialize_provider, {'name': 'foo',
                                                                                                     'cluster': []})

    def test_initialize_provider_with_bad_cluster(self):
        """
        Test the initialize_provider function with settings parameters where the "cluster" key has an invalid value.
        """
        self.assertRaisesConfError(ConfigurationErrorCodes.BAD_CLUSTER, initialize_provider, {'name': 'foo',
                                                                                              'cluster': ''})
        self.assertRaisesConfError(ConfigurationErrorCodes.BAD_CLUSTER, initialize_provider, {'name': 'Hello',
                                                                                              'cluster': 'World!'})

    def test_initialize_provider_with_no_class(self):
        """
        Test the initialize_provider function with settings parameters that have no "class" key.
        """
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_CLASS_KEY, initialize_provider,
                                   {'name': 'foo',
                                    'cluster': cluster_id.TestingApi.MOCK_ID})
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_CLASS_KEY, initialize_provider,
                                   {'name': 'foo',
                                    'cluster': cluster_id.TestingApi.MOCK_ID,
                                    ' class': ''})
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_CLASS_KEY, initialize_provider,
                                   {'name': 'foo',
                                    'cluster': cluster_id.TestingApi.MOCK_ID,
                                    'Class': ''})

    def test_initialize_provider_with_nonstring_class(self):
        """
        Test the initialize_provider function with settings parameters where the "class" key has non-string value.
        """
        self.assertRaisesConfError(ConfigurationErrorCodes.CLASS_NOT_STRING, initialize_provider,
                                   {'name': 'foo',
                                    'cluster': cluster_id.TestingApi.MOCK_ID,
                                    'class': None})
        self.assertRaisesConfError(ConfigurationErrorCodes.CLASS_NOT_STRING, initialize_provider,
                                   {'name': 'foo',
                                    'cluster': cluster_id.TestingApi.MOCK_ID,
                                    'class': -1})
        self.assertRaisesConfError(ConfigurationErrorCodes.CLASS_NOT_STRING, initialize_provider,
                                   {'name': 'foo',
                                    'cluster': cluster_id.TestingApi.MOCK_ID,
                                    'class': tuple()})

    def test_initialize_provider_with_bad_class(self):
        """
        Test the initialize_provider function with settings parameters where the "class" key has a bad value.

        These tests are not exhaustive because there's a separate test suite "ProviderClassTests" below for the
        parse_class function.
        """
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_MODULE, initialize_provider,
                                   {'name': 'foo',
                                    'cluster': cluster_id.TestingApi.MOCK_ID,
                                    'class': 'FooProvider',
                                    'model': model_id.EMOD})
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_CALLABLE_NAME, initialize_provider,
                                   {'name': 'foo',
                                    'cluster': cluster_id.TestingApi.MOCK_ID,
                                    'class': 'foo_module.',
                                    'model': model_id.EMOD})
        self.assertRaisesConfError(ConfigurationErrorCodes.MODULE_IMPORT_ERROR, initialize_provider,
                                   {'name': 'foo',
                                    'cluster': cluster_id.TestingApi.MOCK_ID,
                                    'class': 'job_services.tests.NonExistentModule.FooProvider',
                                    'model': model_id.EMOD})

    def test_initialize_provider_with_no_model(self):
        """
        Test the initialize_provider function with settings parameters that have no "model" key.
        """
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_MODEL_KEY, initialize_provider,
                                   {'name': 'foo',
                                    'cluster': cluster_id.TestingApi.MOCK_ID,
                                    'class': 'job_services.providers.winhpc.WinHpcManifestProvider.WinHpcManifestProvider'})
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_MODEL_KEY, initialize_provider,
                                   {'name': 'foo',
                                    'cluster': cluster_id.TestingApi.MOCK_ID,
                                    'class': 'job_services.providers.winhpc.WinHpcManifestProvider.WinHpcManifestProvider',
                                    'MODEL': 'bar'})
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_MODEL_KEY, initialize_provider,
                                   {'name': 'foo',
                                    'cluster': cluster_id.TestingApi.MOCK_ID,
                                    ' model': 'bar',
                                    'class': 'job_services.providers.winhpc.WinHpcManifestProvider.WinHpcManifestProvider'})

    def test_initialize_provider_with_nonstring_model(self):
        """
        Test the initialize_provider function with settings parameters where the "model" key has non-string value.
        """
        self.assertRaisesConfError(ConfigurationErrorCodes.MODEL_NOT_STRING, initialize_provider,
                                   {'name': 'foo',
                                    'cluster': cluster_id.TestingApi.MOCK_ID,
                                    'model': None,
                                    'class': 'job_services.providers.winhpc.WinHpcManifestProvider.WinHpcManifestProvider'})
        self.assertRaisesConfError(ConfigurationErrorCodes.MODEL_NOT_STRING, initialize_provider,
                                   {'name': 'foo',
                                    'cluster': cluster_id.TestingApi.MOCK_ID,
                                    'model': -1,
                                    'class': 'job_services.providers.winhpc.WinHpcManifestProvider.WinHpcManifestProvider'})
        self.assertRaisesConfError(ConfigurationErrorCodes.MODEL_NOT_STRING, initialize_provider,
                                   {'name': 'foo',
                                    'cluster': cluster_id.TestingApi.MOCK_ID,
                                    'model': [],
                                    'class': 'job_services.providers.winhpc.WinHpcManifestProvider.WinHpcManifestProvider'})

    def test_initialize_provider_with_bad_model(self):
        """
        Test the initialize_provider function with settings parameters where the "model" key has an invalid value.
        """
        self.assertRaisesConfError(ConfigurationErrorCodes.BAD_MODEL, initialize_provider,
                                   {'name': 'foo',
                                    'cluster': cluster_id.TestingApi.MOCK_ID,
                                    'model': '',
                                    'class': 'job_services.providers.winhpc.WinHpcManifestProvider.WinHpcManifestProvider'})
        self.assertRaisesConfError(ConfigurationErrorCodes.BAD_MODEL, initialize_provider,
                                   {'name': 'Hello',
                                    'cluster': cluster_id.TestingApi.MOCK_ID,
                                    'model': 'World!',
                                    'class': 'job_services.providers.winhpc.WinHpcManifestProvider.WinHpcManifestProvider'})

    @mock.patch("job_services.providers.conf.clusters.get")
    def test_initialize_provider_with_unconfigured_cluster(self, mock_get_cluster):
        mock_get_cluster.return_value = None
        param_dict = {'name': 'foo',
                      'cluster': cluster_id.TestingApi.MOCK_ID,
                      'model': '',
                      'class': 'job_services.providers.winhpc.WinHpcManifestProvider.WinHpcManifestProvider'}
        self.assertRaisesConfError(ConfigurationErrorCodes.UNCONFIGURED_CLUSTER, initialize_provider, param_dict)

    def test_get_optional_settings_with_no_optional_settings_defined(self):
        # setup a dictionary with only required keys
        initial_settings = dict()
        for item in REQUIRED_KEYS:
            initial_settings[item] = str(item)
        optional_settings = get_optional_settings(initial_settings, REQUIRED_KEYS)
        self.assertEqual(optional_settings, {})

    def test_get_optional_settings_with_optional_settings_defined(self):
        initial_settings = dict()
        for item in REQUIRED_KEYS:
            initial_settings[item] = str(item)
        initial_settings["optional1"] = "value1"
        initial_settings["optional2"] = "value2"
        optional_settings = get_optional_settings(initial_settings, REQUIRED_KEYS)
        self.assertEqual(optional_settings, {"optional1": "value1", "optional2": "value2"})


def dummy_function():
    """
    A non-class object at the module level.  Used for checking the parse_class method.
    """
    pass # pragma: no cover


class ProviderClassTests(ConfigurationErrorMixin, TestCase):
    """
    Unit tests for parsing names of provider classes.
    """

    def test_parse_class_with_no_class_name(self):
        """
        Test the parse_class function with parameters that have no class names.
        """
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_CALLABLE_NAME, parse_class, '')
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_CALLABLE_NAME, parse_class, '.')
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_CALLABLE_NAME, parse_class, 'module.')

    def test_parse_class_with_bad_class_name(self):
        """
        Test the parse_class function with parameters that are not valid Python identifiers.
        """
        self.assertRaisesConfError(ConfigurationErrorCodes.BAD_CALLABLE_NAME, parse_class, 'module. ')
        self.assertRaisesConfError(ConfigurationErrorCodes.BAD_CALLABLE_NAME, parse_class, 'module.3')
        self.assertRaisesConfError(ConfigurationErrorCodes.BAD_CALLABLE_NAME, parse_class, 'module.3foo')
        self.assertRaisesConfError(ConfigurationErrorCodes.BAD_CALLABLE_NAME, parse_class, 'module.HelloWorld!')
        self.assertRaisesConfError(ConfigurationErrorCodes.BAD_CALLABLE_NAME, parse_class, 'module.foo-bar')

    def test_parse_class_with_no_module_name(self):
        """
        Test the parse_class function with parameters that have no module names.
        """
        self.assertRaisesConfError(ConfigurationErrorCodes.NO_MODULE, parse_class, '.ProviderClass')

    def test_parse_class_with_module_errors(self):
        """
        Test the parse_class function with parameters whose modules cannot be imported
        """
        self.assertRaisesConfError(ConfigurationErrorCodes.MODULE_IMPORT_ERROR, parse_class,
                                   '--abc--.ProviderClass')
        self.assertRaisesConfError(ConfigurationErrorCodes.MODULE_IMPORT_ERROR, parse_class,
                                   'Hello World!.ProviderClass')
        self.assertRaisesConfError(ConfigurationErrorCodes.MODULE_IMPORT_ERROR, parse_class,
                                   'NonExistentModule.ProviderClass')
        self.assertRaisesConfError(ConfigurationErrorCodes.MODULE_IMPORT_ERROR, parse_class,
                                   'sys.NonExistentModule.ProviderClass')
        self.assertRaisesConfError(ConfigurationErrorCodes.MODULE_IMPORT_ERROR, parse_class,
                                   'job_services.NonExistentModule.ProviderClass')
        self.assertRaisesConfError(ConfigurationErrorCodes.MODULE_IMPORT_ERROR, parse_class,
                                   'job_services.tests.NonExistentModule.ProviderClass')

    def test_parse_class_with_undefined_classes(self):
        """
        Test the parse_class function with parameters that have undefined class names
        """
        self.assertRaisesConfError(ConfigurationErrorCodes.UNDEFINED_CALLABLE, parse_class,
                                   'sys.AssumeThereIsNoClassWithThisName')
        self.assertRaisesConfError(ConfigurationErrorCodes.UNDEFINED_CALLABLE, parse_class,
                                   'job_services.UndefinedClass')
        self.assertRaisesConfError(ConfigurationErrorCodes.UNDEFINED_CALLABLE, parse_class,
                                   'job_services.providers.UndefinedClass')

    def test_parse_class_with_non_class_names(self):
        """
        Test the parse_class function with parameters that do not refer Python classes
        """
        self.assertRaisesConfError(ConfigurationErrorCodes.NOT_PY_CLASS, parse_class, 'job_services.providers')
        self.assertRaisesConfError(ConfigurationErrorCodes.NOT_PY_CLASS, parse_class, 'job_services.providers.conf')
        self.assertRaisesConfError(ConfigurationErrorCodes.NOT_PY_CLASS, parse_class,
                                   'job_services.tests.provider_tests.conf_tests.dummy_function')

    def test_parse_class_with_classes_not_derived_from_base(self):
        """
        Test the parse_class function with parameters that are classes not derived from ProviderBase
        """
        self.assertRaisesConfError(ConfigurationErrorCodes.NOT_SUBCLASS, parse_class,
                                   'job_services.providers.conf.ConfigurationErrorCodes')
        self.assertRaisesConfError(ConfigurationErrorCodes.NOT_SUBCLASS, parse_class,
                                   'job_services.tests.provider_tests.conf_tests.ProviderClassTests')

    def test_parse_callable_with_non_callable(self):
        self.assertRaisesConfError(ConfigurationErrorCodes.NOT_PY_CALLABLE, parse_callable,
                                   "simulation_models.model_id")

    def test_parse_callable_with_good_name(self):
        self.assertIs(model_id.is_valid, parse_callable("simulation_models.model_id.is_valid"))
        
    def test_valid_python_identifier(self):
        """
        Test the valid_python_identifier function.
        """
        self.assertTrue(valid_python_identifier('foo'))
        self.assertTrue(valid_python_identifier('foo_bar'))
        self.assertTrue(valid_python_identifier('f'))
        self.assertTrue(valid_python_identifier('_foo'))
        self.assertTrue(valid_python_identifier('Foo'))
        self.assertTrue(valid_python_identifier('foo123'))
        self.assertTrue(valid_python_identifier('WinHpcManifestProvider'))

        self.assertFalse(valid_python_identifier('3'))
        self.assertFalse(valid_python_identifier('3Foo'))
        self.assertFalse(valid_python_identifier(''))
        self.assertFalse(valid_python_identifier(' '))
        self.assertFalse(valid_python_identifier(' foo'))
        self.assertFalse(valid_python_identifier('foo '))
        self.assertFalse(valid_python_identifier('foo.'))
