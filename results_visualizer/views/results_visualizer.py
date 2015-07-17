# PEP 0263
# -*- coding: utf-8 -*-

########################################################################################################################
# VECNet CI - Prototype
# Date: 8/28/13
# Institution: University of Notre Dame
# Primary Authors:
#   Caleb Reinking <Caleb.M.Reinking.2@nd.edu>
########################################################################################################################
"""
    Prototype of EMOD output page
"""
from collections import defaultdict
import datetime
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
import time
from data_services.adapters import EMOD_Adapter
from data_services.models import DimBaseline, DimUser, DimRun, Folder, SimulationOutputFile, Simulation

import json
import csv
import urllib


def as_chart(data, start_time, is_grouped=False):
        """
        This method is one method responsible for formatting the simulation data into a highstock or highchart format.
        This will also convert the timesteps into milliseconds from the epoch (for highstock charts).

        :param data: array of data to be visualized
        :returns: A json object containing a highstock object
        """

        highchart = {
            "chart": {
                "type": "scatter",
                "inverted": False,
                "zoomType": 'xy',
                "width": 650,
                "height": 650
            },
            "scrollbar": {
                "enabled": True
            },
            "tooltip": {
                "enabled": "false",
                "pointFormat": "<span style=\"color:{series.color}\"> {series.name} </span> : <b>{point.y:,.4f}</b><br/> "
            },
            "legend": {
                "enabled": "true"
            },
            "title": {
                "text": ""
            },
            "xAxis": {
                "title": {
                    "text": "Days"
                },
                "categories": "",
                "labels": {
                    "rotation": 270
                }
            },
            "yAxis": {
                "title": {
                    "text": ""
                }
            },
            "series": "",
            "exporting": {
                "enabled": True
            },
            "navigation": {
                "buttonOptions": {
                    "enabled": True
                }
            },
            "credits": {
                "enabled": True
            }
        }

        interval = 1  # day

        return_chart = highchart
        return_chart['chart'] = {}
        return_chart['xAxis'] = {"type": 'datetime'}
        return_chart['series'] = list()

        if is_grouped:
            pinterval = 24 * 3600 * 1000 * interval * int(365/interval)
        else:
            pinterval = 24 * 3600 * 1000 * interval

        return_chart['series'].append({
            "name": "Test Name",
            "data": data,
            "pointStart": time.mktime(start_time.timetuple()) * 1000,
            "pointInterval": pinterval
        })

        return json.dumps(return_chart)


def viewtastic_fetch_scenarios(username, scenario_type):
    user = DimUser.objects.get_or_create(username=username)[0]

    if scenario_type == "private":
        # Get scenarios that are not deleted and are owned by the user making the request
        scenarios = DimBaseline.objects.filter(Q(is_deleted=False) & Q(user=user.id)).order_by('-id')
    elif scenario_type == "public":
        # Get scenarios that are not deleted and are public
        scenarios = DimBaseline.objects.filter(Q(is_deleted=False) & Q(is_public=True)).order_by('-id')
    else:
        raise ValueError("scenario_type of " + str(scenario_type) +
                         "received. scenario_type should be either \"private\" or \"public\"")

    json_scenarios = []

    if scenario_type == "public":
        for scenario in scenarios:
            if scenario.name:
                scenario_json = {"id": scenario.id,
                                 "name": scenario.name}
                json_scenarios.append(scenario_json)
    else:
        # Create a dictionary of children (keys are parents, value is list of children)
        my_folders = defaultdict(list)

        # Add in folder-scenario relations
        for scen in scenarios:
            if scen.folder_id is None:
                my_folders[0].append({'id': scen.id, 'name': scen.name, 'type': 'sim'})
            else:
                if scen.folder_id in my_folders.keys():
                    my_folders[scen.folder_id].append({'id': scen.id, 'name': scen.name, 'type': 'sim'})
                else:
                    my_folders.update({scen.folder_id: [{'id': scen.id, 'name': scen.name, 'type': 'sim'}]})

        # Add in folder-folder relations
        folder_list_all = list(Folder.objects.filter(user=user.id,
                                                     is_deleted=False))
        for folder in folder_list_all:
            if folder.parent is None:
                my_folders[0].append({'id': folder.id, 'name': folder.name, 'type': 'folder'})
            else:
                my_folders[folder.parent.id].append({'id': folder.id, 'name': folder.name, 'type': 'folder'})

        json_scenarios = get_children(0, my_folders, 0)

    return json_scenarios


def get_children(folder, my_folders, depth_gauge):
    json_scenarios = []
    if my_folders[folder] is None or my_folders[folder] == []:
        return json_scenarios
    else:
        for counter, child in enumerate(my_folders[folder]):
            if depth_gauge == 0:
                name_text = '&nbsp;&nbsp;&nbsp;&nbsp;'
            else:
                name_text = '&nbsp;&nbsp;&nbsp;&nbsp;' * depth_gauge
            if child['type'] == 'sim':
                # simulation
                name_text = '&nbsp;&nbsp;&nbsp;&nbsp;' * depth_gauge
                name_text += '(' + str(child['id']) + ') ' + child['name']
                scenario_json = {"id": child['id'], "name": name_text}
            else:
                # folder
                name_text = '&nbsp;&nbsp;'
                name_text += '&nbsp;&nbsp;&nbsp;' * depth_gauge
                name_text += child['name']
                scenario_json = {"id": 0, "name": name_text}

            # add this node to the tree
            json_scenarios.append(scenario_json)
            # get the leaves for this node
            json_scenarios.extend(get_children(child['id'], my_folders, depth_gauge + 1))

    return json_scenarios


def has_valid_runs(request, scenario_id):
    runs = json.loads(viewtastic_fetch_runs(request, scenario_id))
    if len(runs) == 0:
        return False
    elif len(runs[0]['executions']) == 0:
        # print "HI"
        # print runs[0]['id']
        return False
    # else:
    #    print runs
    #     print runs
    #     print json.loads(runs)
    #     print runs[0]
    #     print runs[1]
    return True


def viewtastic_fetch_runs(request, scenario_id):
    """
    For a given scenario, the fetch_runs function fetches all of the runs and returns their names and ids in a
    dictionary.

    :param request: needed for providing a validated username
    :type request: ajax request object
    :param scenario_id: the scenario to fetch the runs for
    :type scenario_id: int
    :return: a dictionary of run names and ids for the given scenario
    """

    adapter = EMOD_Adapter(user_name=request.user.username)
    return_runs = []

    baseline = DimBaseline.objects.get(id=scenario_id)

    if baseline.simulation_group is None:
        runs = DimRun.objects.filter(baseline_key=scenario_id).order_by('-id')

        for run in runs:
            the_run = {'name': run.name, 'id': run.pk}
            the_run_executions = adapter.fetch_executions(run.pk)
            the_run['executions'] = the_run_executions
            return_runs.append(the_run)
    else:
        # Result Simulation ID instead
        sim = baseline.simulation_group.simulations.all()[0]
        return_runs = [{"name": baseline.name,
                        "id": "s%s" % sim.id,
                        "executions": ["s%s" % sim.id]}]

    if request.is_ajax():
        return HttpResponse(content=json.dumps(return_runs), content_type="application/json")

    return return_runs


@never_cache
def viewtastic_fetch_keys(request, run_id):
    """
    For a given run, the fetch_keys function fetches all of the keys and values that
    were swept on for that specific run.

    :param request: needed for providing a validated username
    :type request: ajax request object
    :param run_id: the run to fetch the keys for
    :type run_id: int
    :return: a dictionary of key names and values for the given run
    """

    adapter = EMOD_Adapter(user_name=request.user.username)
    try:
        run_id = int(run_id)
    except ValueError:
        # This is a simulation ID, return empty list
        return HttpResponse(content=json.dumps([]), content_type="application/json")
    keys = adapter.fetch_keys(run_id=run_id)
    return_keys = []
    order_counter = 1

    for element in keys:
        for key, value in sorted(element.iteritems()):
            the_key = {'name': key}

            # Workaround for Bug #6199
            # There is inconsistency between representing numbers in javascript and python.
            # In python, there are two separate types, float and int. 1 (integer) is not the same as 1.0 (float)
            # In contrast, javascript has only one type - number. 1.0 (float) will be represented as 1.
            # As a workaround, we will represent sweep value as a string in visualizer.
            str_value = []
            for val in value:
                str_value.append(str(val))
            the_key['options'] = str_value
            the_key['order'] = order_counter
            order_counter += 1
            return_keys.append(the_key)

    return HttpResponse(content=json.dumps(return_keys), content_type="application/json")


@never_cache
def viewtastic_fetch_channels(request, run_id):
    """
    For a given run, the fetch_channels function fetches all of the channels available for viewing.

    :param request: needed for providing a validated username
    :type request: ajax request object
    :param run_id: the run to fetch the keys for.
    :type run_id: int
    :return: a dictionary of channel ids and channel info (contains title and type for each channel)
    """

    adapter = EMOD_Adapter(user_name=request.user.username)
    try:
        run_id = int(run_id)
    except ValueError:
        # This is a simulation ID, return list of channels in InsectChart
        sim = Simulation.objects.get(id=int(run_id[1:]))
        config = json.loads(sim.simulationoutputfile_set.get(name="InsetChart.json").get_contents())
        return_channels = []
        for channel in config["Channels"]:
            return_channels.append({"id": channel,
                                    "info": {
                                        "title": channel,
                                        "units": "no"
                                        # "type": "minor vector"
                                    }
                                    }
                                   )
    else:
        channels = adapter.fetch_channels(run_id=run_id, as_object=False)
        return_channels = []

        for key, value in channels.iteritems():
            the_channel = {'id': key, 'info': value}
            return_channels.append(the_channel)

    return HttpResponse(content=json.dumps(sorted(return_channels, key=lambda channel: channel['info'])),
                        content_type="application/json")


@never_cache
def viewtastic_download_data(request):
    """
    Given a specific set of chart data, create a csv of all of the raw data points for download
    :param request: the GET value should contain all of the needed chart properties to create the file.
    :return: a csv file HTTPResponse type. SHould open a download dialog on the host browser upon return.
    """
    # since this is a querySet, need to get the data. Should only be one key, but for safety simply
    # overwrite if a second one is found.
    the_chart = json.loads(urllib.unquote(request.POST['json-data']))

    # create a CSV response type
    response = HttpResponse(mimetype='text/csv')

    # give it a file name (this is what it will be saved as)
    response['Content-Disposition'] = 'attachment; filename="VecNet_Data_Export.csv"'

    # create the CSV writer
    csv_writer = csv.writer(response)

    # write out the run name
    csv_writer.writerow(['Run Name:', the_chart.get('runName', '')])

    # EMOD, OM, etc
    csv_writer.writerow(['Simulation Model:', request.session['visualizer_adapter']])

    # The 'Channel' or 'Output' chosen (yAxis label)
    csv_writer.writerow(['Chart Title:', the_chart.get('chartName', '')])

    csv_writer.writerow([])
    csv_writer.writerow(['Series Name', 'Data Values'])

    # use default values in case it wasn't passed in by js
    protected_chart_type = the_chart.get('chartType', 'null')
    protected_categories = the_chart.get('categories', [])

    # TODO: Add start date and timestep for each series

    # boxplot logic will be the death of me. Each chart type comes in with a little different
    # property structure, so have to write custom code for each type right now.
    if protected_chart_type == 'boxplot':
        chart_has_outliers = len(the_chart['series']) > 1
        if chart_has_outliers:  # preprocess the outliers
            outlier_dict = {}
            for outlier_tuple in the_chart['series'][1]['data']:
                try:
                    outlier_dict[outlier_tuple[0]]
                except:  # if it doesn't exist, create an empty list, otherwise simply append
                    outlier_dict[outlier_tuple[0]] = []
                outlier_dict[outlier_tuple[0]].append(outlier_tuple[1])

        for idx, boxplotSeries in enumerate(the_chart['series'][0]['data']):
            try:
                series_name = protected_categories[idx]
            except:
                series_name = 'Error Retrieving Series Name'
            data_row = [series_name, ] + boxplotSeries
            csv_writer.writerow(data_row)
            if chart_has_outliers and outlier_dict.get(idx, False):
                # overall chart has outliers, but more importantly so does this series
                data_row = ['series outliers', ]+outlier_dict[idx]
                csv_writer.writerow(data_row)
    else:  # not a boxplot, right now default is a time series.
        for series in the_chart['series']:
            series_name = series['name']
            data_row = [series_name, ]+series['data']
            csv_writer.writerow(data_row)

    # Return our CSV-type response
    return response


@never_cache
@csrf_exempt
def viewtastic_fetch_data(request):
    """
    For a given execution dictionary, the fetch_data function returns a chart json for insertion into
    a highcharts object.
    This function also returns the channel id for asynchronous data flow and identification reasons.

    :param request: needed for providing a validated username and providing the execution dictionary via the
    packaged GET data.
    :type request: ajax request object
    :return: a dictionary containing the channel id and the associated chart for the selected channel
    """
    temp_chart_json = {}
    temp_chart_json.clear()
    adapter = EMOD_Adapter(user_name=request.user.username)  # get_appropriate_model_adapter(request)

    dict_list = []
    for key in request.POST:
        dict_list.append(json.loads(key))

    # if there weren't any sweeps done, then the execution id needs to be passed to the function.
    the_params = None
    try:
        the_params = dict_list[0]['parameters']
        # Turn the dict of lists into a list of dicts, ordered by the mod order from when the fetch_keys
        # was called
        the_param_list = []
        for sweep_object in the_params:
            the_params[sweep_object]['name'] = sweep_object
            the_param_list.append(the_params[sweep_object])

        final_param_list = []
        for param in sorted(the_param_list, key=lambda sweep: sweep['mod_order']):
            final_param_list.append({param['name']: param['values']})

    except:
        the_execid = dict_list[0]['execution']

    try:
        chart_type = dict_list[0]['chart_type']
    except:
        chart_type = 'time_series'

    try:
        the_aggregation = dict_list[0]['aggregation']
    except:
        the_aggregation = 'daily'

    try:
        the_run = int(dict_list[0]['run_id'])
        the_channel = int(dict_list[0]['channel_id'])
    except:
        # Requesting Simulation data
        sim_id = int(dict_list[0]['run_id'][1:])  # Remove first 's' character
        the_channel = dict_list[0]['channel_id']
        start_date = datetime.datetime(1995, 1, 1)
        insetchartfile = SimulationOutputFile.objects.get(simulation=sim_id, name="InsetChart.json")
        data = json.loads(insetchartfile.get_contents())["Channels"][the_channel]["Data"]
        data = as_chart(data, start_date)

    else:
        # if the parameters aren't available then try getting the data via the execution id
        if the_params is not None:
            if the_aggregation == 'yearly_sum':
                data = adapter.fetch_data(group_by=True,
                                          exec_dict=final_param_list,
                                          run_id=the_run,
                                          channel_id=the_channel,
                                          as_chart=True, as_highstock=True)
            else:
                data = adapter.fetch_data(exec_dict=final_param_list,
                                          run_id=the_run,
                                          channel_id=the_channel,
                                          as_chart=True, as_highstock=True)
        else:
            if the_aggregation == 'yearly_sum':
                data = adapter.fetch_data(group_by=True,
                                          execution_id=the_execid,
                                          run_id=the_run,
                                          channel_id=the_channel,
                                          as_chart=True, as_highstock=True)
            else:
                data = adapter.fetch_data(execution_id=the_execid,
                                          run_id=the_run,
                                          channel_id=the_channel,
                                          as_chart=True, as_highstock=True)

    temp_chart_json = json.loads(data)

    temp_chart_json['chart']['height'] = 335 + (15 * len(temp_chart_json['series']))
    temp_chart_json['chart']['width'] = 500

    temp_chart_json['rangeSelector'] = {'enabled': False}
    real_return_json = dict(channel_id=the_channel,
                            chart_JSON=temp_chart_json,
                            chart_type=chart_type,
                            aggregation=the_aggregation)

    return HttpResponse(content=json.dumps(real_return_json), content_type="application/json")


class ResultView(TemplateView):
    """
    This view is responsible for rendering visualizations for the data warehouse
    """
    @property
    def template_name(self):
        return 'results_visualizer/results_viewer.html'

    def get_context_data(self, **kwargs):
        context = super(ResultView, self).get_context_data(**kwargs)
        print "None"
        context['private_scenarios'] = viewtastic_fetch_scenarios(self.request.user.username, "private")
        context['public_scenarios'] = viewtastic_fetch_scenarios(self.request.user.username, "public")

        return context


class ResultByScenarioView(TemplateView):
    @property
    def template_name(self):
        return 'results_visualizer/results_viewer.html'

    def get_context_data(self, **kwargs):
        context = super(ResultByScenarioView, self).get_context_data(**kwargs)
        if 'scenario_id' in kwargs:
            context['visualizer_scenario_id'] = kwargs['scenario_id']

        return context


class ResultByRunView(TemplateView):
    @property
    def template_name(self):
        return 'results_visualizer/results_viewer.html'

    def get_context_data(self, **kwargs):
        context = super(ResultByRunView, self).get_context_data(**kwargs)
        if 'run_id' in kwargs:
            context['visualizer_run_id'] = kwargs['run_id']
            # Check to make sure the run id is valid,
            # if not then don't preselect anything by sending -1 as the scenario id
            try:
                run = DimRun.objects.get(id=kwargs['run_id'])
                scenario = run.baseline_key
                context['visualizer_scenario_id'] = scenario.id
            except ObjectDoesNotExist:
                context['visualizer_scenario_id'] = -1
            except AttributeError:
                context['visualizer_scenario_id'] = -1
                print "Run " + kwargs['run_id'] + " is missing a scenario."

        return context

class ResultBySimulationView(TemplateView):
    @property
    def template_name(self):
        return 'results_visualizer/results_viewer.html'

    def get_context_data(self, **kwargs):
        context = super(ResultBySimulationView, self).get_context_data(**kwargs)
        if 'simulation_id' in kwargs:
            context['visualizer_run_id'] = 's' + str(kwargs['simulation_id'])
            # Check to make sure the run id is valid,
            # if not then don't preselect anything by sending -1 as the scenario id
            try:
                simulation = Simulation.objects.get(id=kwargs['simulation_id'])
                scenario = DimBaseline.objects.get(simulation_group=simulation.group)
                context['visualizer_scenario_id'] = scenario.id
            except ObjectDoesNotExist:
                context['visualizer_scenario_id'] = -1
            except AttributeError:
                context['visualizer_scenario_id'] = -1
                print "Simulation " + kwargs['simulation_id'] + " is missing a scenario."

        return context
