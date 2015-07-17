"""
The ID constants for all known simulation models.

Example::

    from simulation_models import model_id

    def my_function(sim_model, ...):
        if sim_model == model_id.OPEN_MALARIA:
            # do something special for OpenMalaria
            ...
        else:
            # handle all other simulation models in the same way
            ...
"""

# This module has no import statements, so it can be safely used in a Django project settings file.

# Short strings are used to facilitate debugging
EMOD = 'EMOD'          #: EMOD
OPEN_MALARIA = 'OM'    #: OpenMalaria http://code.google.com/p/openmalaria/wiki/Start

ALL_KNOWN = (EMOD, OPEN_MALARIA)  #: List of all known IDs.
_set_of_all_known = set(ALL_KNOWN)

MAX_LENGTH = 10  #: For use when storing IDs in a database field, e.g. CharField(max_length=model_id.MAX_LENGTH)


def is_valid(mod_id):
    """
    Is an ID a known value?

    :param str mod_id: The model ID to check
    :returns: True or False
    :raises: TypeError if mod_id is not a string.
    """
    if not isinstance(mod_id, basestring):
        raise TypeError('Expected string or unicode, received %s' % str(type(mod_id)))
    return mod_id in _set_of_all_known


def parse(text):
    """
    Parse a model ID from a text string.

    Handles both unicode or ASCII strings.
    Leading and trailing whitespace is ignored.
    Letter case is also ignored.

    :param str text: The string with a model ID.
    :returns: a model ID or None if the string isn't a valid ID.
    """
    text_lower = text.strip().lower()
    for id_ in ALL_KNOWN:
        if text_lower == id_.lower():
            return id_
    return None