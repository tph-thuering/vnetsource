from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from vecnet.simulation import sim_status

from ..models import DimUser, Simulation, SimulationGroup


class SimTimeFieldTests(TestCase):
    """
    Tests for the fields of the Simulation data model that hold time information (when it was started, duration, ...).
    """

    @classmethod
    def setUpClass(cls):
        cls.user = DimUser.objects.create(username='test-user')
        cls.sim_group = SimulationGroup.objects.create(submitted_by=cls.user)

    @classmethod
    def tearDownClass(cls):
        for data_model in Simulation, SimulationGroup, DimUser:
            data_model.objects.all().delete()

    def test_initial_values(self):
        """
        Test a simulation object after it is created -- all the time fields should be None.
        """
        simulation = Simulation.objects.create(group=self.sim_group)
        self.assertIsNone(simulation.started_when)
        self.assertIsNone(simulation.duration)
        self.assertIsNone(simulation.duration_as_timedelta)
        self.assertIsNone(simulation.ended_when)

    def start_simulation(self, simulation):
        now = timezone.now()
        simulation.started_when = now
        simulation.status = sim_status.STARTED_SCRIPT
        return now

    def test_while_running(self):
        """
        Test a simulation object while it's running.
        """
        simulation = Simulation.objects.create(group=self.sim_group)
        self.start_simulation(simulation)
        self.assertIsNone(simulation.duration)
        self.assertIsNone(simulation.duration_as_timedelta)
        self.assertIsNone(simulation.ended_when)

    def test_when_ended(self):
        """
        Test a simulation object after it has ended.
        """
        simulation = Simulation.objects.create(group=self.sim_group)
        start_time = self.start_simulation(simulation)

        # Assume simulation finished successfully
        simulation.status = sim_status.SCRIPT_DONE
        duration = timedelta(hours=2, minutes=10, seconds=37)
        simulation.duration = duration.total_seconds()
        self.assertEqual(simulation.duration_as_timedelta, duration)
        self.assertEqual(simulation.ended_when, start_time + duration)
