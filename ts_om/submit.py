from django.contrib.auth.models import User

from vecnet.simulation import sim_model, sim_status
from vecnet.openmalaria import get_schema_version_from_xml

from data_services.models import DimUser, SimulationGroup, Simulation, SimulationInputFile

from sim_services import dispatcher


def submit(user, xml, version=None):
    # Create Simulation and SimulationGroup
    if isinstance(user, User):
        user = DimUser.objects.get_or_create(username=user.username)[0]
    if isinstance(user, (str, unicode)):
        user = DimUser.objects.get_or_create(username=user)[0]

    sim_group = SimulationGroup(submitted_by=user)
    sim_group.save()
    print sim_group.id

    simulation = add_simulation(sim_group, xml, version=version)
    try:
        dispatcher.submit(sim_group)
        return simulation
    except RuntimeError:
        return None


def submit_group(user, xml_scenarios, version=None):
    # Create Simulation and SimulationGroup
    if isinstance(user, User):
        user = DimUser.objects.get_or_create(username=user.username)[0]
    if isinstance(user, (str, unicode)):
        user = DimUser.objects.get_or_create(username=user)[0]

    sim_group = SimulationGroup(submitted_by=user)
    sim_group.save()
    for scenario in xml_scenarios:
        add_simulation(sim_group, scenario, version=version)
    try:
        dispatcher.submit(sim_group)
        return sim_group
    except RuntimeError:
        return None


def add_simulation(sim_group, xml, version=None, input_file_metadata=None):
    """
    Adds a new simulation for a scenario to a simulation group.

    :param sim_group: The group to add the simulation to.
    :param str xml: The scenario's parameters in XML format.
    :return Simulation: The new simulation.
    """
    assert isinstance(sim_group, SimulationGroup)
    if version is None:
        # Extract schemaVersion from the xml
        version = get_schema_version_from_xml(xml)
    assert version == "32" or version == "30" or version == "33"

    scenario_file = SimulationInputFile.objects.create_file(contents=xml,
                                                            name="scenario.xml",
                                                            metadata="{}",
                                                            created_by=sim_group.submitted_by)
    if input_file_metadata is not None:
        for item in input_file_metadata:
            # Note that scenario_file.metadata is dict after calling create_file
            scenario_file.metadata[item] = input_file_metadata[item]  # "scenario32.xml"
    scenario_file.save()
    print scenario_file.id
    print scenario_file.get_contents()

    simulation = Simulation(group=sim_group,
                            model=sim_model.OPEN_MALARIA,
                            version=version,
                            status=sim_status.READY_TO_RUN)
    simulation.save()
    simulation.input_files.add(scenario_file)
    return simulation
