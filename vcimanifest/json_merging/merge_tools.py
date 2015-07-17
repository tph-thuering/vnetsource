"""
This contains the merging tools needed for the emod_manifest split_execution function.
"""

from copy import deepcopy


def merger(dict1, dict2):
    """
    This method will merge two dictionaries recursively.

    Anytime the dictionary contains a dictionary this method will be called on that dictionary to merge
    """
    merge_dict = dict()
    cpy_dict = deepcopy(dict1)
    for key, value in dict2.iteritems():
        if value == {}:
            cpy_dict[key] = {}
        elif isinstance(value, dict):
            if key in cpy_dict:
                cpy_dict[key] = merger(cpy_dict[key], value)
            else:
                #  At this point there are two options, either its an integer or not.
                #  If its an integer, cpy_dict should be a list, and we should insert
                #  value at that ndx.
                ndx = None
                try:
                    #import pdb; pdb.set_trace()
                    ndx = int(key)
                    #  Only in the case where both the cpy_dict and ndx and value are dictionaries
                    #  do we merge.  Otherwise we insert (no merging lists).
                    if isinstance(value, dict) and isinstance(cpy_dict[ndx], dict):
                        cpy_dict[ndx] = merger(cpy_dict[ndx], value)
                    else:
                        cpy_dict.insert(ndx, value)
                except ValueError:
                    cpy_dict[key] = value
        elif isinstance(value, list):
            if value == []:
                cpy_dict[key] = []
            elif key in cpy_dict:
                cpy_dict[key].extend(value)
            else:
                cpy_dict[key] = value
        else:
            merge_dict.update({key: value})
    if isinstance(cpy_dict, list):
        return cpy_dict
    cpy_dict.update(merge_dict)
    return cpy_dict

def xpath_to_dict(dict1, truncate=False):
    """
    This method assumes the dictionary passed in is a key value paire as follows:
        - The key is an xpath
        - The value is what should be set at that xpath
    """
    trun_dict = {
        list: [],
        dict: {},
        str: "",
        unicode: "",
        int: None,
        float: None
    }
    new_dict = dict()
    for key, value in dict1.iteritems():
        if key == 'mode': continue
        sub_dict = dict()
        keys = key.split('/')
        if truncate:
            sub_dict.update({keys[-1]: trun_dict[type(value)]})
        else:
            sub_dict.update({keys[-1]: value})
        for path in reversed(key.split('/')[:-1]):
            sub_dict = {path: sub_dict}
        new_dict = merger(new_dict, sub_dict)
    return new_dict

def merge_list(dict1, changeObj, mode=None):
    """
    This method will merge a change object into a dictionary

    The list of changes should be as follows
    TODO: Add change documentation here
    Each merge is done recursively.
    """
    cpy_dict = deepcopy(dict1)
    changeList = changeObj['Changes']
    for change in changeList:
        if isinstance(change, dict):
            if mode == 'TRUNCATE':
                trunc_dict = xpath_to_dict(change, truncate=True)
                cpy_dict = merger(cpy_dict, trunc_dict)
            change_dict = xpath_to_dict(change)
            cpy_dict = merger(cpy_dict, change_dict)
        elif isinstance(change, (str, unicode)):
            mode_dict = {
                '+': None,
                '-': 'TRUNCATE',
                '~': 'MERGE'
            }
            mode = mode_dict.get(change[0], None)
            name = change.strip('+-~')
            cpy_dict = merge_list(cpy_dict, changeObj[name], mode=mode)
    return cpy_dict
