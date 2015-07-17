# DKDK this is for Ben's result only

import json
import os

# Ben's output
# weather  : af, am, aw, bsh, cwa
# demo     : 50y, 55y, 60y
# eir      : 2, 10, 100

def get_calibrated_species(weather, demo, eir, species):
    # DKDK below needs to be hardcorded or pass the argument or something
    base_dir = os.path.dirname(os.path.abspath(__file__))
    calib_base_dir = os.path.join(base_dir, "data")

    # DKDK please note that Ben shared calibrated config file without pre-calibrated config so the file config.json
    # below is actually calibrated config.json
    config_new_json = os.path.join(calib_base_dir, weather, demo, "config.json")
    with open(config_new_json) as jsondata_config_new:
        config_new = json.load(jsondata_config_new)

    # DKDK be careful to check whether eir will be integer or string - assumed here that eir is integer
    vector_name = species + '-' + str(eir) + '.0'
    # print "vector_name: %s \n" % vector_name

    vector_param = config_new["parameters"]["Vector_Species_Params"][vector_name]

    ### DKDK add "EIR" key
    vector_param["EIR"] = eir

    return json.dumps(vector_param, indent=4, sort_keys=True, separators=(',', ': '))


if __name__ == '__main__':
    weather = 'aw'
    demo = '60y'
    eir = 100
    species = 'minor vector'
    returned_string = get_calibrated_species(weather, demo, eir, species)
    print returned_string
