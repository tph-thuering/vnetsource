"""
Utility code for Django applications.
"""


def make_choices_tuple(choices, get_display_name):
    """
    Make a tuple for the choices parameter for a data model field.

    :param choices: sequence of valid values for the model field
    :param get_display_name: callable that returns the human-readable name for a choice

    :return: A tuple of 2-tuples (choice, display_name) suitable for the choices parameter
    """
    assert callable(get_display_name)
    return tuple((x, get_display_name(x)) for x in choices)
