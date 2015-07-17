########################################################################################################################
# VECNet CI - Prototype
# Date: 6/18/2013
# Institution: University of Notre Dame
# Primary Authors:
#   Robert Jones <Robert.Jones.428@nd.edu>
########################################################################################################################

from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.generic.edit import CreateView
from django.db.models import Q
from lib.templatetags.base_extras import set_notification
import ast
import json
import re

from ts_emod.models.models import Species, ConfigData
from ts_emod.forms import SpeciesCreateForm
from ts_emod.views.EditWizardView import edit_wizard


def saveSpecies(request, species_id=None):
    """Function to save Species DB Objects
    """
    if request.method == 'POST':
        # check to see where to redirect to (who called this)
        if request.POST.get("calling_page") == 'edit_wizard':
            return_to = edit_wizard
        # else:
        #     return_to = scenario_wizard

        # check to make sure an empty name wasn't passed
        if request.POST.get("my_name") == '':
            set_notification('alert-error', '<strong>Error!</strong> Unable to save vector - name cannot be empty.',
                             request.session)
            return redirect(return_to, step="species")

        # get keys from orig_json_obj
        settings_data = []
        counter = 0

        habitat = []
        factor = []

        my_json = '{"' + request.POST.get("my_name").replace(' ', '_') + '": {'
        for key in request.POST.keys():  # request.POST.get("orig_json_obj").keys:
            if re.search(r"(^json_)", key):
                settings_data.append('config.json/parameters/' + str(key).replace('json_', '') + '='
                                     + str(request.POST.get(key)))

                if 'json_Required_Habitat_Factor' in key:
                    continue

                # Handle special combo box Arrays: Habitat_Type, Required_Habitat_Factor
                if 'json_Habitat_Type' in key:
                    habitat.append(str(request.POST.get(key)))
                    if request.POST.get('json_Required_Habitat_Factor_'+str(key.split('_')[-1])) == '':
                        factor.append(0)
                    else:
                        factor.append(int(ast.literal_eval(request.POST.get('json_Required_Habitat_Factor_'
                                                                            + str(key.split('_')[-1])))))
                    continue

                counter += 1
                if counter > 1:
                    my_json += ','

                #TODO: escape quote characters to avoid injection of a new json key,value through the new species form
                my_json += '"' + str(key).replace('json_', '') + '": ' + str(request.POST.get(key))

        if len(habitat) > 0:
            my_json += ', "Habitat_Type": ' + str(habitat).replace("'", '"')
            my_json += ', "Required_Habitat_Factor": ' + str(factor)

        my_json += '} }'

        species = Species()

        #TODO: change this check to look at the template + db vectors, instead of only in the db
        name_already_exists = Species.objects.filter(Q(created_by=request.user)
                                                     | Q(is_public=1)).filter(
                                                         name=request.POST.get("my_name").replace(' ', '_'))
        if name_already_exists:
            set_notification('alert-error', '<strong>Error!</strong> Unable to save vector.'
                             'There is already a species with the name "'
                             + request.POST.get("my_name").replace(' ', '_') +
                             '". Please choose a unique name and try again.', request.session)
        else:
            species = Species(name=request.POST.get("my_name").replace(' ', '_'),
                              orig_json_obj="",  # request.POST.get("orig_json_obj")
                              json=my_json,
                              # settings=settings_data  # request.POST.get("settings")
                              created_by=request.user,
                              is_public=0)
            species.save()
            set_notification('alert-success', '<strong>Success!</strong> Vector created successfully! "'
                             + request.POST.get("my_name").replace(' ', '_') +
                             '" is now available for selection.', request.session)

    #if species.id is None:
    return redirect(return_to, step="species")
    #else:
    #    request.session['species_id'] = str(species.id)
    #    kwargs = {"species_id": str(species.id)}
    #    return redirect(return_to, step="species", **kwargs)


def deleteSpecies(request, species_id):
    """Function to delete Species DB Objects
    """
    try:
        species_to_delete = Species.objects.get(id=species_id)
        species_to_delete.delete()
        set_notification('alert-success', '<strong>Success!</strong> You have successfully deleted the species.',
                         request.session)
    except:
        print 'Error deleting species with id: %s' % species_id
        set_notification('alert-error', '<strong>Success!</strong> You have successfully deleted the scenario.',
                         request.session)
    return redirect('ts_emod_scenario_browse')


def getFormSpecies(request, species_name):
    """Return the form for creating a new Species

    - input: species_name to use to populate the initial form
    - output: form prepopulated with values specified by input (and species from template or DW)
    """
    my_species = ""
    new_intervention_form = SpeciesCreateForm()
    new_intervention_form.fields['json'].label = ''

    try:
        my_json = ConfigData.objects.get(type='JSONConfig', name='default_emod_vector').json
        if type(my_json) in (str, unicode):
            my_json = json.loads(my_json)
    except:
        print "========= Error in TS_EMOD: getFormSpecies. =========="
        my_json = ""

    # attempt to get "overwrite values" from session, then db
    # - then apply these values to the "ConfigData" used to build the form
    if species_name not in ('default', 'default_emod_vector'):
        if 'scenario_config' in request.session:
            my_config = request.session['scenario_config']
        else:
            try:
                my_config = request.session['config.json']  # <-- required for old work-flow
            except KeyError:
                pass

        if species_name in my_config['parameters']['Vector_Species_Params'].keys():
            # get default form values from template
            my_species = my_config['parameters']['Vector_Species_Params'][species_name]
        else:
            # get default form values from db
            my_species = Species.objects.get(Q(is_public=1) | Q(created_by=request.user), name=species_name).json
            my_species = ast.literal_eval(my_species)[species_name]

        # change text to json
        if type(my_species) in (str, unicode):
            my_species = json.loads(my_species)

        # apply the appropriate values to the form config
        for key in my_species.keys():
            try:
                my_json[key]['default'] = my_species[key]
            except KeyError:
                pass

            # set up the special values for the combo box
            if key == 'Habitat_Type':
                my_dict = {}
                for i in range(len(my_species[key])):
                    my_dict.update({my_species[key][i]: my_species['Required_Habitat_Factor'][i]})
                for i in range(len(my_json[key]['choices'])):
                    try:
                        my_json[key]['values_defaults'][i] = my_dict[my_json[key]['choices'][i]]
                    except:
                        pass

    if type(my_json) == dict:
        my_json = json.dumps(my_json)

    try:
        new_intervention_form.fields['json'].initial = my_json
    except KeyError:
        new_intervention_form.fields['json'].label = 'No parameters found. Please contact System Administrator.'

    #return HttpResponse(new_intervention_form.as_grid_div())
    return HttpResponse(new_intervention_form.as_p())
