"""
This holds all the functions required to fetch the simulation type from a given object.
"""


def emod_sim_type_from_template(template):
    """
    This takes an EMOD template instance and determines its simulation type.

    :param template: DimTemplate instance that is of model type EMOD
    :returns: String containing simulation type
    """
    file = template.dimfiles_set.filter(
        file_type='config.json'
    ).extra(
        select={'sim_type': "content::json->'parameters'->'Simulation_Type'"}
    )
    return str(file[0].sim_type)


def om_sim_type_from_template(template):
    """
    This takes an Open Malaria template instance and determines its simulation type.

    :param template: DimTemplate instance that is of model type OM (Open Malaria)
    :returns: String containing simulation type
    """
    file = template.dimfiles_set.filter(
        file_type='input.xml'
    ).extra(
        select={'sim_type': "xpath_exists('/scenario/entomology/vector',content::xml)"}
    )

    if file[0].sim_type:
        return 'VECTOR'
    else:
        return 'NON_VECTOR'
