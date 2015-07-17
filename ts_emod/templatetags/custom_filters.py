########################################################################################################################
# VECNet CI - Prototype
# Date: 4/5/2013
# Institution: University of Notre Dame
# Primary Authors:
########################################################################################################################

# Imports that are external to the expert_emod app

import re
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.datastructures import SortedDict

register = template.Library()

@register.filter

@stringfilter
def replace(string, args):
    """A custom filter to replace characters by regular expression
    """
    search  = args.split(args[0])[1]
    replace = args.split(args[0])[2]
    return re.sub( search, replace, string )

@register.filter(name='template_dict_sort')
def template_dict_sort(value):
    """A custom filter to sort dictionaries
    """
    if isinstance(value, dict):
        new_dict = SortedDict()
        key_list = value.keys()
        key_list.sort()
        for key in key_list:
            new_dict[key] = value[key]
        return new_dict
    elif isinstance(value, list):
        new_list = list(value)
        new_list.sort()
        return new_list
    else:
        return value
    template_dict_sort.is_safe = True
