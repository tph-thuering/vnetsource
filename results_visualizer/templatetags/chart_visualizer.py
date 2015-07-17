########################################################################################################################
# VECNet CI - Prototype
# Date: 1/15/2014
# Institution: University of Notre Dame
# Primary Authors: Caleb Reinking
########################################################################################################################
from data_services.models import DimBaseline
from results_visualizer.views.results_visualizer import viewtastic_fetch_runs, viewtastic_fetch_scenarios
from django import template
from django.core.exceptions import ObjectDoesNotExist

register = template.Library()

@register.inclusion_tag('results_visualizer/tags/chart_visualizer.html', takes_context=True)
def chart_visualizer(context, scenario_id=-1, run_id=-1):
    """
    This provides a list of scenarios and runs for the template tag

    IMPORTANT!!!!
    This template tag requires the following javascripts be included on any page using the visualizer::

        <script type="text/javascript" src="https://code.highcharts.com/stock/2.0.4/highstock.js"></script>
        <script type="text/javascript" charset="utf-8" src="https://code.highcharts.com/stock/2.0.4/modules/exporting.js"></script>
        <script type="text/javascript" src="{{ STATIC_URL }}results_visualizer/js/esults_visualizer.js"></script>

    :param context: used to get the user name and fetch appropriate
    :return: a dictionary of scenarios and runs to iterate over in the template tag
    """

    dataDict = {} #initialize our empty dictionary

    dataDict['private_scenarios'] = viewtastic_fetch_scenarios(context["request"].user.username, "private")
    dataDict['public_scenarios'] = viewtastic_fetch_scenarios(context["request"].user.username, "public")

    # Ensure the scenario exists
    try:
        DimBaseline.objects.get(id=scenario_id)
        scenario_exists = True
    except ObjectDoesNotExist:
        scenario_exists = False

    if scenario_id != -1 and scenario_exists:
        dataDict['scenario_choice'] = scenario_id
        print "scenario_choice = " + str(dataDict['scenario_choice'])
        dataDict['runs'] = viewtastic_fetch_runs(context['request'], scenario_id=scenario_id)
        if run_id != -1:
            dataDict['run_choice'] = run_id
            print "run_choice = " + str(dataDict['run_choice'])

    return dataDict