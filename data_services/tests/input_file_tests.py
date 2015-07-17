import hashlib

from django.test import TestCase

from ..models import DimUser, Simulation, SimulationGroup, SimulationInputFile


class SimInputFileTests(TestCase):
    """
    Tests for the data model for simulation input files.
    """

    @classmethod
    def setUpClass(cls):
        cls.user = DimUser.objects.create(username='test-user')
        cls.sim_group = SimulationGroup.objects.create(submitted_by=cls.user)
        cls.simulation = Simulation.objects.create(group=cls.sim_group)

    @classmethod
    def tearDownClass(cls):
        for data_model in Simulation, SimulationGroup, DimUser:
            data_model.objects.all().delete()

    def assertContentsEqual(self, input_file, expected_contents):
        self.assertIsInstance(input_file, SimulationInputFile)
        retrieved_contents = input_file.get_contents()
        self.assertEqual(retrieved_contents, expected_contents)
        expected_hash = hashlib.md5(expected_contents).hexdigest()
        self.assertEqual(input_file.metadata[input_file.MetadataKeys.CHECKSUM], expected_hash)

    def test_one_file(self):
        """
        Test with an input file associated with just one simulation.
        """
        contents = 'Four score and seven years ago, our forefathers ...'
        sim_input_file = SimulationInputFile.objects.create_file(contents, created_by=self.user)
        self.assertContentsEqual(sim_input_file, contents)

        sim_input_file.simulations.add(self.simulation.id)
        self.assertEqual(sim_input_file.simulations.count(), 1)
        self.assertEqual(sim_input_file.simulations.all()[0], self.simulation)

    def test_file_shared_by_many(self):
        """
        Test where an input file is shared by multiple simulations.
        """
        contents = "Roses are red, violets are blue, ..."
        sim_input_file = SimulationInputFile.objects.create_file(contents, created_by=self.user)
        self.assertContentsEqual(sim_input_file, contents)

        simulation2 = Simulation.objects.create(group=self.sim_group)
        simulation3 = Simulation.objects.create(group=self.sim_group)

        sim_input_file.simulations.add(self.simulation, simulation2, simulation3)
        self.assertEqual(sim_input_file.simulations.count(), 3)
        expected_pks = (self.simulation.id, simulation2.id, simulation3.id)
        for simulation in sim_input_file.simulations.all():
            self.assertIn(simulation.id, expected_pks)

    def test_foo(self):
        """
        Test where a simulation has multiple input files.
        """
        empty_contents = ''
        empty_input_file = SimulationInputFile.objects.create_file(empty_contents, created_by=self.user)
        self.assertContentsEqual(empty_input_file, empty_contents)
        empty_input_file.simulations.add(self.simulation)

        json_contents = '''
            {
                "foo_parameter": 42,
                "bar_parameter": "/path/to/data.csv"
            }
        '''
        json_input_file = SimulationInputFile.objects.create_file(json_contents, created_by=self.user)
        self.assertContentsEqual(json_input_file, json_contents)
        json_input_file.simulations.add(self.simulation)

        self.assertEqual(self.simulation.input_files.count(), 2)
        for input_file in (empty_input_file, json_input_file):
            self.assertIsInstance(self.simulation.input_files.get(id=input_file.id), SimulationInputFile)

    def test_open_for_reading(self):
        """
        Test the open_for_reading() method of an input file.
        """
        empty_om_scenario = """
            <?xml version='1.0' encoding='UTF-8' standalone='no'?>
            <om:scenario xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'
                         name='name'
                        schemaVersion='32'
                        xsi:schemaLocation='http://openmalaria.org/schema/scenario_32 scenario_32.xsd'
                        xmlns:om='http://openmalaria.org/schema/scenario_32'
                        analysisNo='0'
                        wuID='0'>
            </om:scenario>"
        """
        sim_input_file = SimulationInputFile.objects.create_file(empty_om_scenario, created_by=self.user)
        with sim_input_file.open_for_reading() as f:
            retrieved_contents = f.read()
        self.assertEqual(retrieved_contents, empty_om_scenario)
