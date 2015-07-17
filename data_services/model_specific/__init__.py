"""
This is where the model specific code lives.  As we prepare to refactor to extend the ORM instead of build a
structure around it (like the model adapters), model specific code and a way to access that code has to
exist.  This is *NOT* the permanent home for this code, only a temporary home until the refactoring of
Data Services start.
"""

from sim_type import emod_sim_type_from_template, om_sim_type_from_template

sim_type = {
    'EMOD': emod_sim_type_from_template,
    'Open Malaria': om_sim_type_from_template
}