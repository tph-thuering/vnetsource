import cStringIO
import datetime

from django.contrib.auth.models import User
from tastypie.test import ResourceTestCase
from vecnet.simulation import sim_status

from ..models import DimBinFiles, DimUser, Simulation, SimulationGroup, SimulationInputFile, SimulationOutputFile
from ..rest_api import api  # To ensure API singleton is instantiated, so that get_resource_uri method calls work.
                            # See https://groups.google.com/forum/#!topic/django-tastypie/VZoFaBossnw
from ..rest_api.resources import InputFileResource, OutputFileResource
from VECNet import test_settings


class DimBinFileTests(ResourceTestCase):
    """
    Tests for the DimBinFile resources.
    """

    def setUp(self):
        super(DimBinFileTests, self).setUp()

        self._passwords = dict()
        self.user = self.create_user('sally', 'secret')
        self.input_file = DimBinFiles.objects.create(file_name='sample input file',
                                                     description='A sample input file for testing',
                                                     file_type='text',
                                                     file_hash='AAAA',
                                                     content='jjjjjjjjjjjjjjjfasdfkajsfj sflaks f;askjf;askjf')

    def create_user(self, username, password):
        user = User.objects.create_user(username, '%s@example.org' % username, password)
        self._passwords[user] = password
        return user

    def login(self, user):
        assert isinstance(user, User)
        self.assertTrue(self.api_client.client.login(username=user.username, password=self._passwords[user]))

    def logout(self):
        self.api_client.client.logout()

    def test_get_info_json(self):
        """
        Test getting the information for an input file in JSON format.
        """
        self.login(self.user)
        file_url = '/data_services/api/v1/dim_bin_files/%s/?format=json' % self.input_file.pk
        response = self.api_client.get(file_url)
        self.assertValidJSONResponse(response)

        json_obj = self.deserialize(response)
        model_fields = (
            'description',
            'file_hash',
            'file_name',
            'file_type',
            'id',
            'is_deleted',
            'version',
        )
        api_fields = (
            'resource_uri',
            'size',
        )
        all_fields = model_fields + api_fields
        self.assertKeys(json_obj, all_fields)
        for key in model_fields:
            field_value = getattr(self.input_file, key)
            if isinstance(field_value, datetime.datetime):
                field_value = field_value.isoformat()
            elif not isinstance(field_value, (int, float, basestring)):
                field_value = str(field_value)
            self.assertEqual(json_obj[key], field_value)
        self.assertEqual(json_obj['size'], len(self.input_file.content))

        self.logout()


class InputFileTests(ResourceTestCase):
    """
    Tests for the InputFile resources.
    """

    @classmethod
    def setUpClass(cls):
        cls.user = DimUser.objects.create(username='test-user')
        cls.contents = '''
            <?xml version = "1.0"?>
                <input-parameters>
                    <foo>42</foo>
                    <bar>/path/to/data.csv</bar>
                </input-parameters>
        '''
        cls.input_file = SimulationInputFile.objects.create_file(cls.contents, name='input_parameters.xml',
                                                                 created_by=cls.user)
        cls.file_url = InputFileResource().get_resource_uri(cls.input_file)

    @classmethod
    def tearDownClass(cls):
        for data_model in Simulation, SimulationGroup, DimUser:
            data_model.objects.all().delete()

    def test_get_info_json(self):
        """
        Test getting the information for an input file in JSON format.
        """
        response = self.api_client.get(self.file_url)
        self.assertValidJSONResponse(response)

        expected_values = {
            'id': self.input_file.pk,
            'name': self.input_file.name,
            'created_when': self.input_file.created_when.isoformat(),
            'metadata': self.input_file.metadata,
        }
        json_obj = self.deserialize(response)
        self.assertDictContainsSubset(expected_values, json_obj)

    def test_download(self):
        """
        Test the downloading of an input file's contents.
        """
        download_url = self.file_url + 'download/'
        response = self.api_client.get(download_url)
        self.assertHttpOK(response)
        contents = ''.join(response.streaming_content)
        self.assertEqual(contents, self.contents)


# Sample OpenMalaria files

CTSOUT_TXT = """
timestep	simulated EIR
0	0.0752771
1	0.0817232
2	0.0801483
3	0.0783576
4	0.076365
5	0.0743008
6	0.072511
7	0.0708406
8	0.0690646
9	0.0673053
"""

OUTPUT_TXT = """
1	1	0	1000
1	1	3	480
2	1	0	1000
2	1	3	497
3	1	0	1000
3	1	3	450
4	1	0	1000
4	1	3	451
5	1	0	1000
5	1	3	463
"""


def str_to_lines(s):
    """
    Split a string into lines, preserving the newline characters at the end of each line.
    """
    return cStringIO.StringIO(s).readlines()


class OutputFileTests(ResourceTestCase):
    """
    Tests of POST requests to the output-files endpoint.
    """

    @classmethod
    def setUpClass(cls):
        cls.resource_endpoint = OutputFileResource().get_resource_uri()
        test_user = DimUser.objects.create(username='test-user')
        sim_group = SimulationGroup.objects.create(submitted_by=test_user)
        cls.simulation = Simulation.objects.create(group=sim_group)

    @classmethod
    def tearDownClass(cls):
        for data_model in Simulation, SimulationGroup, DimUser:
            data_model.objects.all().delete()

    def setUp(self):
        super(OutputFileTests, self).setUp()
        self.simulation.status = sim_status.STARTED_SCRIPT
        self.simulation.save()

    def check_error_info(self, response, expected_error):
        """
        Check the error information in the response's body.
        """
        error_info = self.deserialize(response)
        self.assertEqual(error_info['error'], expected_error)
        if 'error_details' in error_info:
            error_details = error_info['error_details']
            self.assertIsInstance(error_details, basestring)
            if test_settings.verbosity >= 2:
                print '\n  error =', error_info['error']
                print '  error_details = "%s"' % error_details
            return error_details  # In case the caller wants to do further checking

    def check_sim_status(self, expected_status):
        updated_simulation = Simulation.objects.get(id=self.simulation.id)
        self.assertEqual(updated_simulation.status, expected_status)

    def test_invalid_json(self):
        """
        Test where the request body has invalid JSON.
        """
        invalid_json = '{ "foo": }'  # Missing value for key

        # In order to have the "data" parameter treated as a string and not as a dictionary, we have to use the Django
        # test client rather than the Tastypie's test client.  Furthermore, we have to give that client an explicit
        # content_type.
        response = self.client.post(self.resource_endpoint, content_type='application/json', data=invalid_json)
        self.assertHttpBadRequest(response)
        self.check_error_info(response, OutputFileResource.Errors.INVALID_JSON)
        self.check_sim_status(sim_status.STARTED_SCRIPT)

    def test_not_json_object(self):
        """
        Test where the request body is not a JSON object.
        """
        array = [1, 2, 3]
        response = self.api_client.post(self.resource_endpoint, data=array)
        self.assertHttpBadRequest(response)
        self.check_error_info(response, OutputFileResource.Errors.NOT_JSON_OBJECT)
        self.check_sim_status(sim_status.STARTED_SCRIPT)

    def test_no_id_on_client(self):
        """
        Test where the request body is missing the "id_on_client" name.
        """
        body = {
            "output_files": {
            }
        }
        response = self.api_client.post(self.resource_endpoint, data=body)
        self.assertHttpBadRequest(response)
        self.check_error_info(response, OutputFileResource.Errors.NO_ID_ON_CLIENT)
        self.check_sim_status(sim_status.STARTED_SCRIPT)

    def test_bad_id(self):
        """
        Test where the "id_on_client" is not a valid integer.
        """
        body = {
            "id_on_client": ".7",
            "output_files": {
            }
        }
        response = self.api_client.post(self.resource_endpoint, data=body)
        self.assertHttpBadRequest(response)
        self.check_error_info(response, OutputFileResource.Errors.INVALID_ID)
        self.check_sim_status(sim_status.STARTED_SCRIPT)

    def test_unknown_id(self):
        """
        Test where the "id_on_client" is not a valid PK for a simulation.
        """
        body = {
            "id_on_client": "9999999",
            "output_files": {
            }
        }
        response = self.api_client.post(self.resource_endpoint, data=body)
        self.assertHttpBadRequest(response)
        self.check_error_info(response, OutputFileResource.Errors.INVALID_ID)
        self.check_sim_status(sim_status.STARTED_SCRIPT)

    def test_no_output_files(self):
        """
        Test where the request body is missing the "output_files" name.
        """
        body = {
            "id_on_client": str(self.simulation.id),
        }
        response = self.api_client.post(self.resource_endpoint, data=body)
        self.assertHttpBadRequest(response)
        self.check_error_info(response, OutputFileResource.Errors.NO_OUTPUT_FILES)
        self.check_sim_status(sim_status.OUTPUT_ERROR)

    def test_files_not_dict(self):
        """
        Test where the value of "output_files" is not a dictionary (JSON object).
        """
        body = {
            "id_on_client": str(self.simulation.id),
            "output_files": ["foo"],
        }
        response = self.api_client.post(self.resource_endpoint, data=body)
        self.assertHttpBadRequest(response)
        self.check_error_info(response, OutputFileResource.Errors.FILES_NOT_OBJECT)
        self.check_sim_status(sim_status.OUTPUT_ERROR)

    def test_unknown_names(self):
        """
        Test where there are unknown names for output files.
        """
        body = {
            "id_on_client": str(self.simulation.id),
            "output_files": {
                'bar.csv':    'unknown',
                'ctsout.txt': '',
                'foo.dat':    'unknown',
                'output.txt': '',
            },
        }
        response = self.api_client.post(self.resource_endpoint, data=body)
        self.assertHttpBadRequest(response)
        error_details = self.check_error_info(response, OutputFileResource.Errors.UNKNOWN_NAMES)
        for name, status in body['output_files'].iteritems():
            if status == 'unknown':
                self.assertTrue(name in error_details)
        self.check_sim_status(sim_status.OUTPUT_ERROR)

    def test_0_files(self):
        """
        Test where the "output_files" object has 0 entries.
        """
        body = {
            "id_on_client": str(self.simulation.id),
            "output_files": {
            }
        }
        response = self.api_client.post(self.resource_endpoint, data=body)
        self.assertHttpAccepted(response)
        self.check_sim_status(sim_status.SCRIPT_DONE)

    def test_1_file(self):
        """
        Test where the "output_files" object has 1 entry.
        """
        SimulationOutputFile.objects.all().delete()
        body = {
            "id_on_client": str(self.simulation.id),
            "output_files": {
                "ctsout.txt": CTSOUT_TXT,
            }
        }
        response = self.api_client.post(self.resource_endpoint, data=body)
        self.assertHttpAccepted(response)
        self.assertEqual(SimulationOutputFile.objects.count(), 1)
        sim_out_file = SimulationOutputFile.objects.all()[0]
        self.assert_file_is_ctsout_txt(sim_out_file)
        self.check_sim_status(sim_status.SCRIPT_DONE)

    def assert_file_is_ctsout_txt(self, sim_out_file):
        self.check_output_file(sim_out_file, 'ctsout.txt', CTSOUT_TXT)

    def assert_file_is_output_txt(self, sim_out_file):
        self.check_output_file(sim_out_file, 'output.txt', OUTPUT_TXT)

    def check_output_file(self, sim_out_file, expected_name, expected_contents):
        self.assertEqual(sim_out_file.simulation, self.simulation)
        self.assertEqual(sim_out_file.name, expected_name)
        self.assertEqual(sim_out_file.get_contents(), expected_contents)

    def test_1_file_with_lines(self):
        """
        Test where the "output_files" object has 1 entry where the file contents is an array of strings (one per file
        line).
        """
        SimulationOutputFile.objects.all().delete()
        body = {
            "id_on_client": str(self.simulation.id),
            "output_files": {
                "ctsout.txt": str_to_lines(CTSOUT_TXT),
            }
        }
        response = self.api_client.post(self.resource_endpoint, data=body)
        self.assertHttpAccepted(response)
        self.assertEqual(SimulationOutputFile.objects.count(), 1)
        sim_out_file = SimulationOutputFile.objects.all()[0]
        self.assert_file_is_ctsout_txt(sim_out_file)
        self.check_sim_status(sim_status.SCRIPT_DONE)

    def test_file_line_not_str(self):
        """
        Test where the "output_files" object has 1 entry where the file contents is an array but one of its element is
        not a string.
        """
        body = {
            "id_on_client": str(self.simulation.id),
            "output_files": {
                "ctsout.txt": (
                    'foo bar',
                    'Hello World',
                    None,
                ),
            }
        }
        response = self.api_client.post(self.resource_endpoint, data=body)
        self.assertHttpBadRequest(response)
        self.check_error_info(response, OutputFileResource.Errors.LINE_NOT_STRING)
        self.check_sim_status(sim_status.OUTPUT_ERROR)

    def test_not_str_or_array(self):
        """
        Test where the "output_files" object has 1 entry where the file contents is not a string or an array.
        """
        body = {
            "id_on_client": str(self.simulation.id),
            "output_files": {
                "ctsout.txt": { 'answer': 42 },
            }
        }
        response = self.api_client.post(self.resource_endpoint, data=body)
        self.assertHttpBadRequest(response)
        self.check_error_info(response, OutputFileResource.Errors.NOT_STR_OR_ARRAY)
        self.check_sim_status(sim_status.OUTPUT_ERROR)

    def test_2_files(self):
        """
        Test where the "output_files" object has 2 entries.
        """
        SimulationOutputFile.objects.all().delete()
        body = {
            "id_on_client": str(self.simulation.id),
            "output_files": {
                "ctsout.txt": CTSOUT_TXT,
                "output.txt": OUTPUT_TXT,
            }
        }
        response = self.api_client.post(self.resource_endpoint, data=body)
        self.assertHttpAccepted(response)
        self.assertEqual(SimulationOutputFile.objects.count(), 2)
        sim_out_files = SimulationOutputFile.objects.all().order_by('name')

        ctsout_file = sim_out_files[0]
        self.assert_file_is_ctsout_txt(ctsout_file)

        output_file = sim_out_files[1]
        self.assert_file_is_output_txt(output_file)

        self.check_sim_status(sim_status.SCRIPT_DONE)


    def test_2_files_with_lines(self):
        """
        Test where the "output_files" object has 2 entries, both with their contents as array of strings.
        """
        SimulationOutputFile.objects.all().delete()
        body = {
            "id_on_client": str(self.simulation.id),
            "output_files": {
                "ctsout.txt": str_to_lines(CTSOUT_TXT),
                "output.txt": str_to_lines(OUTPUT_TXT),
            }
        }
        response = self.api_client.post(self.resource_endpoint, data=body)
        self.assertHttpAccepted(response)
        self.assertEqual(SimulationOutputFile.objects.count(), 2)
        sim_out_files = SimulationOutputFile.objects.all().order_by('name')

        ctsout_file = sim_out_files[0]
        self.assert_file_is_ctsout_txt(ctsout_file)

        output_file = sim_out_files[1]
        self.assert_file_is_output_txt(output_file)

        self.check_sim_status(sim_status.SCRIPT_DONE)
