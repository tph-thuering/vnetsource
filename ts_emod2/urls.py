from django.conf.urls import patterns, url

from ts_emod2.views.IndexView import IndexView
from ts_emod2.views.MySimulationsView import MySimulationsView
from ts_emod2.views.PublicSimulationsView import PublicSimulationsView
from ts_emod2.views.SimulationUploaderView import SimulationUploaderView

from ts_emod2.views.DetailsView import DetailsView
from ts_emod2.views.InterventionView import InterventionView
from ts_emod2.utils.launch import launch_scenario
from ts_emod2.utils.publicize_privatize_scenario import publicize_scenario, privatize_scenario
from ts_emod2.views.InterventionView2 import InterventionView2

from ts_emod2.views.JSONEditorView import JSONEditorView
from ts_emod2.utils.weather_chart_data import get_weather_chart_data
from ts_emod2.utils.file_transfer import download, upload

from ts_emod2.utils.conversion import convert_baseline_to_scenario
from ts_emod2.utils.misc_functions import copy_scenario, delete_scenarios


urlpatterns = patterns('ts_emod.views',
    url(r'^$', IndexView.as_view(), name='ts_emod2.index'),
    url(r'^my_simulations/$', MySimulationsView.as_view(), name='ts_emod2.my_simulations'),
    url(r'^public_simulations/$', PublicSimulationsView.as_view(), name='ts_emod2.public_simulations'),
    url(r'^simulation_uploader/$', SimulationUploaderView.as_view(), name='ts_emod2.simulation_uploader'),

    # Details page
    url(r'^details/(?P<scenario_id>\d+)/$', DetailsView.as_view(), name='ts_emod2.details'),
    url(r'^intervention/(?P<scenario_id>\d+)/$', InterventionView.as_view(), name='ts_emod2.intervention'),
    url(r'^intervention2/(?P<scenario_id>\d+)/$', InterventionView2.as_view(), name='ts_emod2.intervention2'),
    url(r'^launch/(?P<scenario_id>\d+)/$', launch_scenario, name='ts_emod2.launch'),
    url(r'^publicize/(?P<scenario_id>\d+)/$', publicize_scenario, name='ts_emod2.publicize_scenario'),
    url(r'^privatize/(?P<scenario_id>\d+)/$', privatize_scenario, name='ts_emod2.privatize_scenario'),

    url(r'^json_editor/(?P<file_type>\w+\-*\w+)/(?P<scenario_id>\d+)/$', JSONEditorView.as_view(), name='ts_emod2.json_editor'),  # Example file_type: config, temperature-json, etc
    url(r'^weather_chart_data/(?P<scenario_id>\d+)/$', get_weather_chart_data, name='ts_emod2.get_weather_chart_data'),
    url(r'^download/(?P<file_type>\w+\-*\w+\-*\w+\-*\w+)/(?P<scenario_id>\d+)/$', download, name='ts_emod2.download'),  # Example file_type: config, temperature-json, binned-report-json, vector-species-report-json, etc
    url(r'^upload/(?P<file_type>\w+\-*\w+\-*\w+\-*\w+)/(?P<scenario_id>\d+)/$', upload, name='ts_emod2.upload'),  # Example file_type: config, temperature-json, binned-report-json, vector-species-report-json, etc

    url(r'^convert/(?P<baseline_id>\d+)/$', convert_baseline_to_scenario, name='ts_emod2.convert'),
    url(r'^copy_scenario/(?P<scenario_id>\d+)/$', copy_scenario, name='ts_emod2.copy_scenario'),
    url(r'^delete_scenarios/$', delete_scenarios, name='ts_emod2.delete_scenarios'),
)