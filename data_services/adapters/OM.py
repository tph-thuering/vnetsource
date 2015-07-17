########################################################################################################################
# VECNet CI - Prototype
# Date: 05/02/2013
# Institution: University of Notre Dame
# Primary Authors:
#   Lawrence Selvy <Lawrence.Selvy.1@nd.edu>
########################################################################################################################
import base64
import hashlib
import requests
import zlib

from model_adapter import Model_Adapter

from data_services.models import SimulationGroup, Simulation

class FakeRun:
    pass

class OM_Adapter(Model_Adapter):
    """This is the Open Maleria (OM) Adapter Class

    This class take information from the data warehouse and the digital library (if necesasry)
    and transforms it into the appropriate data for the OM Model.  One task is finding a list of
    locations that contain "complete" data.  Complete data is defined as a location having all the
    data necessary to run the OM Model
    """

    #: Location of the CSV file containing location and link data
    csv_url = 'http://dl-vecnet.crc.nd.edu/downloads/tt44pm93m'
    #: Model type id, 1 for EMOD, 2 for OM
    model_id = 2
    #: Xpath for seed.  This will be used when generating the manifest file
    seed_path = 'input.xml//model/parameters'
    #: Input file list
    inputFiles = ['input.xml']

    def send_run_to_cluster(self, user = 'Test', experiment_number = -1,
            run_number = -1, manifest_string=None):
        #try:
        manifest_hash = hashlib.sha1(manifest_string).hexdigest()
        compressed_manifest = base64.encodestring(zlib.compress(manifest_string))
        r = requests.post('http://vecnet02.crc.nd.edu:8000/submit',
                              data={
                                  'user_name': self.user.username,
                                  'manifest_hash': manifest_hash,
                                  'manifest': compressed_manifest,
                                  'experiment_number': experiment_number,
                                  'run_number': run_number
                              }
            )
        #except:
        #    raise Exception("Error submitting manifest to compute cluster")
        
    def launch_run(self, run_id, cluster='', reps_per_exec=1, scenario_string=''):
        """ This is the launch run method (overrides the base Model_Adapter
        class method)

        This method will take a run id, cluster string (currently not
        implemented), and reps_per_exec and will use these to unpack the run
        into unique executions, save those executions, and the create spaces for
        replications.

        :param run_id: Id of the run to be launched
        :type run_id: int
        :param cluster: String of cluster name (not currently implemented)
        :type cluster: str
        :param reps_per_exec: Number of replications requested per execution
        :type reps_per_exec: int
        :param scenario_string: XML Experiment Manifest
        :type scenario_string: str
        :returns: A tuple containing the number of replications created and
                    number of executions
        """

        raise(NotImplementedError("Not Implemented"))

    def fetch_experiments(self, experiment_id=-1, as_object=False, get_All=False, with_public=True, has_data=False):
        if as_object:
            raise NotImplementedError("Not implemented")
        sim_groups = SimulationGroup.objects.filter(submitted_by = self.user)
        experiments = dict()
        for sim_group in sim_groups:
            experiments[sim_group.id] = {
                "name": "%s" % sim_group.id,
                "description": ""
            }
        return experiments


    def fetch_runs(self, experiment_id=-1, run_id=-1, loc_ndx=-1, as_object=False, get_All=False, has_data=False):
        """
        This method is responsible for fetching the runs contained by a specific experiment or a specific run (pending
        on whether run_id is specified.  The as_object flag determined whether a queryset or dictionary is returned.
        get_All determines if 'deleted' runs are returned with non-deleted runs.

        :param experiment_id: ID of the experiment for which runs should be fetched
        :type experiment_id: int
        :param run_id: ID of the run to be fetched
        :type run_id: int
        :param as_object: Determines whether a queryset is returned (True) or a dictionary
        :type as_object: Boolean
        :param get_All: Determines whether 'deleted' experiments are returned (True) or not (Default)
        :returns: Either a dictionary or a queryset
        :raises: ObjectDoesNotExist
        """
        sim_group = SimulationGroup.objects.get(id=experiment_id)
        if as_object:
            if run_id != -1:
                simulation = Simulation.objects.get(id=run_id)
                fake_run = FakeRun()
                fake_run.name = str(simulation.id)
                fake_run.pk = simulation.id
                return [fake_run]
            else:
                simulations = Simulation.objects.filter(group=sim_group)
                fake_runs = []
                for simulation in simulations:
                    fake_run = FakeRun()
                    fake_run.name = str(simulation.id)
                    fake_run.pk = simulation.id
                    fake_runs.append(fake_run)
                return fake_runs

        if not as_object:
            return_simulations = dict()
            if run_id != -1:
                simulation = Simulation.objects.get(id=run_id)
                return_simulations[simulation.id] = {
                "name": "%s" % simulation.id,
                "description": "",
                "executions": {simulation.id: {"name":"%s" % simulation.id}}
                }
            else:
                simulations = Simulation.objects.filter(group = sim_group)
                for simulation in simulations:
                        return_simulations[simulation.id] = {
                        "name": "%s" % simulation.id,
                        "description": "",
                        "executions": {simulation.id: {"name":"%s" % simulation.id}}
                }

        return return_simulations

    def fetch_executions(self, run_id):
        return [run_id]

    def fetch_channels(self, execution_id=-1, run_id=-1, file_name='', as_object=False):
        if as_object:
            raise NotImplementedError("as_object=True is not supported in OM adapter")
        scenario = Simulation.objects.get(id = run_id)
        # get input and output files, pass them to the Yingjie's OM libtrary
        # get list of all channels and encode them:
        # channel_id * 1000 + age_group
        return {"channel":1000}


    def fetch_keys(self, **kwargs):
        # Always return empty list for now
        return list()

    def fetch_data(self, execution_id=-1, exec_dict=None, run_id=-1, channel_id=-1, as_chart=False, destination='',
                   with_ts=False, channel_name='', channel_type='', as_object=False, as_highstock=False,
                   group_by=False):
        """
        This fetch data method now is an interface for the RunData class.  This will allow the adapter
        to fetch data based on an execution id, channel id, channel name, execution dictionary, etc.  Given
        how flexibile this must be, the RunData class was formed.  This can be simplified by refactoring to
        *kwargs and passing kwargs into RunData

        :param execution_id: Execution id for which data should be fetched
        :type execution_id: int
        :param exec_dict: Dictionary describing an execution
        :type exec_dict: dict
        :param run_id: Constraint on which runs to search for dictionary searching
        :type run_id: int
        :param channel_id: (Optional) Channel id for which data should be fetched
        :type channel_id: int
        :param as_chart: (Optional) Boolean that allows a chart object to be returned or a dictionary
        :type as_chart: bool
        :param destination: (Optional) Div tag that the highstock chart should fill
        :type destination: str or unicode
        :param with_ts: (Defaults False) Boolean that dictates whether an array of timesteps should be returned
                        alongside the data
        :type with_ts: bool
        :param channel_name: (Optional) Name of the channel to be fetched
        :type channel_name: str or unicode
        :param channel_type: (Optional) Type of the channel to be fetched (mosquito type or demographic range)
        :type channel_type: str or unicode
        :param as_object: (Defaults False) Allows a queryset to be returned instead of a dictionary
        :type as_object: bool
        :param group_by: Flag that determines whether to group the data returned by the call into yearly segments
        :type group_by: bool
        """
        raise(NotImplementedError("Not Implemented"))
