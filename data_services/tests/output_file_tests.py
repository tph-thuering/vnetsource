import hashlib

from django.test import TestCase

from ..models import DimUser, Simulation, SimulationGroup, SimulationOutputFile


class SimOutputFileTests(TestCase):
    """
    Tests for the data model for simulation output files.
    """

    @classmethod
    def tearDownClass(cls):
        for data_model in Simulation, SimulationGroup, DimUser:
            data_model.objects.all().delete()

    def test_one_file(self):
        user = DimUser.objects.create(username='test-user')
        sim_group = SimulationGroup.objects.create(submitted_by=user)
        simulation = Simulation.objects.create(group=sim_group)
        contents = 'Four score and seven years ago, our forefathers ...'
        sim_out_file = SimulationOutputFile.objects.create_file(contents, simulation=simulation)
        retrieved_contents = sim_out_file.get_contents()
        self.assertEqual(retrieved_contents, contents)
        expected_hash = hashlib.md5(contents).hexdigest()
        self.assertEqual(sim_out_file.metadata[sim_out_file.MetadataKeys.CHECKSUM], expected_hash)