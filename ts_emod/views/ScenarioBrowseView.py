########################################################################################################################
# VECNet CI - Prototype
# Date: 03/07/2014
# Institution: University of Notre Dame
# Primary Authors:
#   Robert Jones <Robert.Jones.428@nd.edu>
########################################################################################################################
from collections import defaultdict
from data_services.adapters.EMOD import EMOD_Adapter
from data_services.data_api import EMODBaseline
from data_services.models import DimBaseline, DimModel, DimRun, DimTemplate, DimUser, Folder
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from lib.templatetags.base_extras import set_notification
from ts_repr.views.creation.DetailsView import derive_autoname

from ts_emod.forms import named_baseline_forms

import ast
import datetime
import json


class ScenarioBrowseView(TemplateView):
    """Class to implement Run list view

    - Output: HTML detail view of all "available" scenarios based on is_public and user id/created_by
    """
    template_name = 'ts_emod/scenario/scenario_browse.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """
        Accepts a request argument plus arguments, and returns a HTTP response.
        """
        return super(ScenarioBrowseView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Extension of get_context_data

        Add context data to drive menu nav highlights, breadcrumbs and pagers.
        """
        context = super(ScenarioBrowseView, self).get_context_data(**kwargs)
        the_request = self.request

        context['nav_button'] = 'scenario_browse'

        pager_size = the_request.POST.get('pager_size') or the_request.GET.get('pager_size')
        if pager_size is None:
            pager_size = 10
        else:
            pager_size = int(pager_size)

        # Get list of folders in this folder (if no current folder, include folders with no parent)
        if 'folder_id' in kwargs.keys():
            current_folder = kwargs['folder_id'] or the_request.POST.get('folder_id') or the_request.GET.get('folder_id') or None
            context['current_folder'] = Folder.objects.get(pk=current_folder)
        else:
            current_folder = None

        # get a list of all scenarios in order to get count of sims in each folder
        scenario_list_all = list(DimBaseline.objects.filter(user=DimUser.objects.get(username=self.request.user.username),
                                                is_deleted=False))
        my_count = {}
        for scen in scenario_list_all:
            if scen.folder_id in my_count.keys():
                my_count[scen.folder_id] += 1
            else:
                my_count[scen.folder_id] = 1

        # create a dictionary of children (keys are parents, value is list of children)
        folder_list_all = list(Folder.objects.filter(user=DimUser.objects.get(username=self.request.user.username),
                                                     is_deleted=False))
        my_dict = defaultdict(list)

        for folder in folder_list_all:
            if folder.id in my_count.keys():
                counter = ' (' + str(my_count[folder.id]) + ')'
            else:
                counter = ''
            if folder.parent is None:
                my_dict[0].append({'id': folder.id, 'name': folder.name, 'child_count': counter})
            else:
                my_dict[folder.parent.id].append({'id': folder.id, 'name': folder.name, 'child_count': counter})

        current_found = 0  # Set flag that deterimines if the current folder has been visited in the tree

        if None in my_count.keys():
            counter_root = ' (' + str(my_count[None]) + ')'
        else:
            counter_root = ''

        folder_tree = '{title: "My Simulations' + counter_root + '", folder: true, expanded: true'
        if current_folder is None:
            folder_tree += ', active: true'
            current_found = 1

        # context['folder_tree'] = '{title: "My Tororo Folder full of Simulations (and folders) in home folder ", folder: true }, ' \
        #                          '{title: "Folder 2", folder: true, ' \
        #                              'children: [ ' \
        #                                 '{ title: "Sub-item 2.1", folder: true }, ' \
        #                                 '{ title: "Sub-item 2.2" }] }, ' \
        #                          '{ title: "Item 3" }'
        # without root:
        # context['folder_tree'] = '{title: "Solomon Islands", folder: true}, {title: "Second folder", folder: true, children: [ {title: "subfolder", folder: true}] }'
        #folder_tree = add_children(0, my_dict)
        # with root:
        # context['folder_tree'] = '{title: "My Simulations", folder: true, children: [ {title: "Solomon Islands", folder: true}, {title: "Second folder", folder: true, children: [ {title: "subfolder", folder: true}] }] }'

        folder_tree += add_children(0, my_dict, current_folder, current_found) + '}'

        context['folder_tree'] = str(folder_tree)

        # Get list of scenarios
        scenario_list = list(DimBaseline.objects.filter(user=DimUser.objects.get(username=self.request.user.username),
                                                        folder=current_folder,
                                                        is_deleted=False))

        if scenario_list is None:
            return context

        # sort descending by id (for those old scenarios that all have the same old time_created
        scenario_list = sorted(scenario_list, key=lambda x: x.id, reverse=True)
        # sort descending by time_saved (version)
        scenario_list = sorted(scenario_list, key=lambda x: x.last_modified, reverse=True)

        # merge folders into scenario list
        # - show folders in file list
        #scenario_list = folder_list + scenario_list

        # Flag scenarios that are representative
        for scenario in scenario_list:
            # Hack for now. I don't remember if it is still needed, but I will fix it later. Not currently important.
            if scenario.description == "Made with representative workflow" and not scenario.metadata:
                scenario.metadata = json.dumps({'representative': ''})
                scenario.save()
            if scenario.metadata:
                metadata = json.loads(scenario.metadata)

                if 'representative' in metadata:
                    scenario.is_representative = True
                    if 'is_complete' in metadata['representative']:
                        scenario.representative_is_complete = metadata['representative']['is_complete']
                    else:
                        scenario.representative_is_complete = False
                    scenario.name = derive_autoname(scenario)
                else:
                    scenario.is_representative = False

        paginator = Paginator(scenario_list, pager_size)
        page = int(the_request.GET.get('page') or 1)

        try:
            scenarios = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            scenarios = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            scenarios = paginator.page(paginator.num_pages)

        scenario_count = len(scenario_list)

        context['pager_size'] = pager_size
        context['scenarios'] = scenarios
        context['scenario_range'] = range(paginator.num_pages)
        context['scenario_count'] = scenario_count
        context['current_start'] = (page-1)*pager_size + 1
        context['current_stop'] = min(scenario_count, (page-1)*pager_size + pager_size)
        context['my_username'] = self.request.user.username

        # get locations (need name from dict by id)
        adapter = EMOD_Adapter(self.request.user.username)
        template_list = adapter.fetch_template_list()
        location_dict = adapter.fetch_locations()  # gets list based on EMOD_buffer list in model_adapter.py

        # determine which step edit buttons link to
        step_list = [i[0] for i in named_baseline_forms]
        for scenario in scenario_list:
            if scenario._meta.object_name != 'Folder':
                try:
                    # check to see if it has a campaign file (besides the empty default)
                    if scenario.is_approved:
                        my_scenario = EMODBaseline.from_dw(pk=scenario['id'])
                        try:
                            scenario_campaign = json.dumps(ast.literal_eval(my_scenario.get_file_by_type('campaign').content),
                                                           sort_keys=True, indent=4, separators=(',', ': '))
                        except (AttributeError, ObjectDoesNotExist):
                            try:
                                # if file list was returned, use last file
                                scenario_campaign = json.dumps(ast.literal_eval(
                                    my_scenario.get_file_by_type('campaign')[my_scenario.get_file_by_type('campaign').count()
                                                                             - 1].content), sort_keys=True, indent=4,
                                                               separators=(',', ': '))
                            except ObjectDoesNotExist:
                                pass

                        if len(json.loads(scenario_campaign)['Events']) > 0:
                            scenario['has_interventions'] = 1

                    if scenario.template:
                        scenario.location_name = str(DimTemplate.objects.get(id=scenario.template.id).location_key)

                        # add model version to scenario
                        scenario.model_version = DimTemplate.objects.get(id=scenario.template.id)\
                            .model_version.replace('emod ',  '')
                except:
                    pass
        return context

    # Add context to posting
    def post(self, request, **kwargs):
        context = self.get_context_data()
        return self.render_to_response(context)


def delete_scenario(request, scenario_id):
    """Function to allow deletion of scenario DB Objects
    """
    my_folder = None
    try:
        my_scenario = EMODBaseline.from_dw(pk=scenario_id,
                                           user=DimUser.objects.get_or_create(username=request.user.username)[0])

        my_folder = my_scenario.dimbaseline.folder_id
        my_scenario.delete()
        if my_scenario.dimbaseline.is_deleted:
            set_notification('alert-success', '<strong>Success!</strong> You have successfully deleted the simulation '
                             + my_scenario._name, request.session)
    except:
        print 'Error deleting scenario with id: %s' % scenario_id
        set_notification('alert-error', '<strong>Error!</strong> Simulation was not deleted.', request.session)

    if my_folder is None:
        # return to the home/root folder
        return redirect("ts_emod_scenario_browse")
    else:
        # return to the scenario's folder
        return redirect("ts_emod_scenario_browse", folder_id=str(my_folder))


def delete_run(request, scenario_id, run_id):
    """Function to allow deletion of run DB Objects
    """
    try:
        #  adapter = EMOD_Adapter(request.user.username)
        my_run = DimRun.objects.get(pk=run_id)
        my_name = my_run.name

        if request.user.is_authenticated() \
           and str(DimBaseline.objects.get(id=scenario_id).user) == str(request.user.username):
            #  adapter.delete_run(int(run_id))
            my_run.is_deleted = True
            my_run.time_deleted = datetime.datetime.now()
            my_run.save()

            set_notification('alert-success', '<strong>Success!</strong> You have successfully deleted the run '
                                              + my_name, request.session)
        else:
            set_notification('alert-error', '<strong>Error!</strong> Please log in before deleting. '
                                            'Run was not deleted.', request.session)
    except:
        print 'Error deleting run with id: %s' % run_id
        set_notification('alert-error', '<strong>Error!</strong> Run was not deleted.', request.session)

    return redirect("ts_emod_scenario_details", scenario_id=str(scenario_id))


def duplicate_scenario(request, scenario_id):
    """ Function to allow duplication of scenario DB Objects """
    if not request.user.is_authenticated():
        set_notification('alert-error', 
                         '<strong>Error!</strong> Please log in before copying. Simulation was not copied.',
                         request.session)
    else:
        # Save a copy of the scenario
        try:
            old_scenario = EMODBaseline.from_dw(pk=int(scenario_id))
            my_copy_id = old_scenario.dimbaseline.copy()

            set_notification('alert-success', '<strong>Success!</strong> The simulation ' + old_scenario._name
                                              + ' has been copied.  You are now viewing the copy.', request.session)
            return redirect("ts_emod_scenario_details", scenario_id=my_copy_id)
        except:
            print 'Error copying the scenario.'
            set_notification('alert-error', '<strong>Error!</strong> Error copying the scenario.', request.session)

            return redirect("ts_emod_scenario_details", scenario_id=scenario_id)


def run_to_scenario(request, run_id):
    """ Function to allow duplication of run DB Objects """
    if not request.user.is_authenticated():
        set_notification('alert-error', '<strong>Error!</strong> Please log in before duplicating. '
                                        'Run was not duplicated.', request.session)
        return redirect("ts_emod_scenario_browse")
    else:
        # Save a copy of the run to Adapter/DW
        try:
            adapter = EMOD_Adapter(request.user.username)
            old_run = adapter.fetch_runs(run_id=int(run_id), as_object=True)
            # create empty scenario
            new_scenario = request.session['scenario'] = EMODBaseline(
                name=old_run.name + ' copy',
                description='Duplicate of ' + old_run.name,
                model=DimModel.objects.get(model='EMOD'),
                user=DimUser.objects.get_or_create(username=request.user.username)[0]
            )

            new_scenario.template = DimTemplate.objects.get(id=old_run.template_key_id)

            new_scenario.model_version = new_scenario.template.model_version

            # get input files for run
            file_dict = old_run.get_input_files()
            new_scenario.add_file_from_string('campaign', 'campaign.json', file_dict['campaign.json'],
                                              description="Added during duplication from run.")
            new_scenario.add_file_from_string('config', 'config.json', file_dict['config.json'],
                                              description="Added during duplication from run.")

            # ToDo: get bin input files for run (from run's template)
            # - for now, user will have to edit, and location step will provide them

            new_scenario.save()

            set_notification('alert-success', '<strong>Success!</strong> The run ' + old_run.name
                                              + ' has been duplicated.', request.session)
        except:
            print 'Error saving the duplicate run to scenario: %s' % old_run.name
            set_notification('alert-error', '<strong>Error!</strong> Error duplicating the run '
                                            + old_run.name + '.', request.session)
            return redirect("ts_emod_scenario_browse")

    return redirect("ts_emod_scenario_details", scenario_id=str(new_scenario.id))


def add_children(folder, my_dict, current_folder, current_found):
    """Function to return fancytree children for a given folder dictionary

    :param folder: the folder for which we need the children
    :param my_dict: dictionary containing all the folders and their children
    :param current_folder: This is the "current folder" in the context of the page: which folder is "active" or displayed
            - this node will be flagged as active
    :param current_found: have we passed the current folder in traversing the tree? (0 = no, 1 = yes)
            - used to determine: (folders current and above are flagged as expanded)
    :returns: fancytree children structure

    trivial case: no children (just folder id and necessary flags)
    else process children and recurse (to approach trvial case)
    typically start with root folder (key = 0)

    ToDo: siblings of current should not be expanded
    """
    text = ', id: "' + str(folder) + '"'

    if current_found == 0:
        text += ', expanded: true'

    if str(folder) == current_folder:
        text += ', active: true'
        current_found = 1

    if my_dict[folder] is None or my_dict[folder] == []:
        return text
    else:
        text += ', children: [ '
        for counter, child in enumerate(my_dict[folder]):
            if counter > 0:
                text += '}, '
            text += '{title: "' + child['name'] + child['child_count'] + '", folder: true'
            text += add_children(child['id'], my_dict, current_folder, current_found)
        text += '}] '

        #print "======= ERROR in TS_EMOD folder code ======="
        #print "Error: ", node
    return text
