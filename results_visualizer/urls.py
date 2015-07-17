from django.conf.urls import patterns, url
from django.views.generic import TemplateView
from results_visualizer.views.results_visualizer import viewtastic_fetch_data, \
    viewtastic_download_data, ResultView, viewtastic_fetch_runs, \
    viewtastic_fetch_keys, viewtastic_fetch_channels, ResultByScenarioView, ResultByRunView, ResultBySimulationView

urlpatterns = patterns('results_visualizer.views',
    url(r'^alt/$', TemplateView.as_view(template_name="results_visualizer/rv_index_alt.html"), name='results_viewer_index_alt'),

    # data fetching urls for ajax calls
    url(r'^export/$', viewtastic_download_data, name="results_viewer_download"),
    url(r'^data/(?P<scenario_id>\d+)/$', viewtastic_fetch_runs, name="results_viewer.runs"),
    url(r'^data/\d+/(?P<run_id>\w+)/keys/$', viewtastic_fetch_keys, name="results_viewer.keys"),
    url(r'^data/\d+/(?P<run_id>\w+)/channels/$', viewtastic_fetch_channels, name="results_viewer.channels"),
    url(r'^data/\d+/\w+/data/$', viewtastic_fetch_data, name="results_viewer_data"),

    url(r'^$', ResultView.as_view(), name='results_viewer.index'),
    url(r'^scenario/(?P<scenario_id>\d+)/$', ResultByScenarioView.as_view(), name='results_viewer.scenario'),
    url(r'^run/(?P<run_id>\d+)/$', ResultByRunView.as_view(), name='results_viewer.run'),
    url(r'^simulation/(?P<simulation_id>\d+)/$', ResultBySimulationView.as_view(), name='results_viewer.simulation'),
)