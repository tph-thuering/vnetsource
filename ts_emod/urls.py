########################################################################################################################
# VECNet CI - Prototype
# Date: 4/5/2013
# Institution: University of Notre Dame
# Primary Authors:
#   Robert Jones <Robert.Jones.428@nd.edu>
########################################################################################################################

# Imports that are external to the ts_emod app

from django.conf.urls import patterns, url, include
from django.views.generic import TemplateView

# Imports that are internal to the ts_emod app

from ts_emod.views.IndexView import IndexView
from ts_emod2.views.InterventionView import InterventionView
from ts_emod.views.InterventionToolView import intervention_tool, saveIntervention, deleteIntervention, \
    getFormIntervention
from ts_emod.views.LaunchTool import launch_tool_view
from ts_emod.views.NoteView import note_create_view, saveNote
from ts_emod.views.SweepToolView import sweep_tool, get_range_from_schema

from ts_emod.views.ScenarioBrowseView import ScenarioBrowseView
from ts_emod.views.ScenarioBrowsePublicView import ScenarioBrowsePublicView
from ts_emod.views.ScenarioDetailView import ScenarioDetailView, download_csv_file
from ts_emod.views.BaselineWizardView import baseline_wizard
from ts_emod.views.DownloadView import download_view
from ts_emod.views.EditWizardView import edit_wizard
from ts_emod.views.FolderView import folder_delete, folder_move, folder_rename, folder_save
from ts_emod.views.JsonEditView import JsonEditView

from ts_emod.views.RunDetailView import RunDetailView
from ts_emod.views.RunMetadataDetailView import RunMetadataDetailView
from ts_emod.views.ScenarioCreateByTemplateView import scenarioCreateByTemplate
from ts_emod.views.TemplateDetailView import TemplateDetailView
from ts_emod.views.UploadView import upload_view

from results_visualizer.views.results_visualizer import ResultView, ResultByScenarioView, ResultByRunView

## URLconf for the ts_emod app
#
urlpatterns = patterns('ts_emod.views',
                       url(r'^$', IndexView.as_view(), name='ts_emod_index'),

                       url(r'^run/(?P<run_id>\d+)/note/create/$', note_create_view, name='ts_emod_run_note_create'),
                       url(r'^run/note/save/+(?P<run_id>\d+)?', saveNote, name='ts_emod_note_save'),

                       ##################  Folder routes  ##################
                       url(r'^folder/delete/+(?P<folder_id>\d+)/$', folder_delete, name='ts_emod_folder_delete'),
                       url(r'^folder/move/$', folder_move, name='ts_emod_folder_move'),
                       url(r'^folder/move/+(?P<folder_id>\d+)/+(?P<item_id>\d+)/+(?P<item_type>\d+)/$', folder_move,
                           name='ts_emod_folder_move'),
                       url(r'^folder/rename/$', folder_rename, name='ts_emod_folder_rename'),
                       url(r'^folder/rename/+(?P<folder_id>\d+)/+(?P<name>.+?)/$', folder_rename,
                           name='ts_emod_folder_rename'),
                       url(r'^folder/save/$', folder_save, name='ts_emod_folder_save'),
                       url(r'^folder/save/+(?P<folder_id>\d+)/$', folder_save, name='ts_emod_folder_save'),

                       ##################  Intervention Tool  ##################
                       # url(r'^intervention/(?P<step>.+)/(?P<scenario_id>[-\d]+)/$', intervention_tool,
                       #     name='ts_intervention_tool_step'),
                       # url(r'^intervention/(?P<step>.+)/$', intervention_tool, name='ts_intervention_tool_step'),
                       url(r'^scenario/intervention/delete/(?P<intervention_id>\d+)/$',
                           deleteIntervention, name='ts_emod_intervention_delete'),
                       url(r'^scenario/intervention/save/$', saveIntervention,
                           name='ts_emod_intervention_save'),
                       url(r'^scenario/intervention/form/$', getFormIntervention,
                           name='ts_emod_intervention_form'),
                       url(r'^scenario/intervention/form/(?P<form_name>[\w]+)/$',
                           getFormIntervention, name='ts_emod_intervention_form'),

                       # New intervention stuff
                       url(r'^intervention/(?P<scenario_id>\d+)/$', InterventionView.as_view(), name='ts_intervention_tool_step'),

                       ##################  Launch Tool  ##################
                       url(r'^launchtool/(?P<step>.+)/(?P<scenario_id>\d+)/run/(?P<run_id>\d+)/$', launch_tool_view,
                           name='ts_emod_launch_tool'),
                       url(r'^launchtool/(?P<step>.+)/(?P<scenario_id>\d+)/$', launch_tool_view,
                           name='ts_emod_launch_tool'),
                       url(r'^launchtool/(?P<step>.+)/$', launch_tool_view, name='ts_emod_launch_tool'),


                       ##################  Sweep Tool  ##################
                       url(r'^sweep/(?P<step>.+)/(?P<scenario_id>[-\d]+)/(?P<run_id>[-\d]+)/$', sweep_tool,
                           name='ts_sweep_tool_step'),
                       url(r'^sweep/(?P<step>.+)/(?P<scenario_id>[-\d]+)/$', sweep_tool,
                           name='ts_sweep_tool_step'),
                       url(r'^sweep/(?P<step>.+)/$', sweep_tool, name='ts_sweep_tool_step'),
                       url(r'^get_range/$', get_range_from_schema, name='ts_emod_get_range_from_schema'),

                       ##################  Scenario  ##################
                       url(r'^scenario/create/(?P<step>.+)/(?P<folder_id>[-\d]+)/$', scenarioCreateByTemplate, name='ts_ScenarioCreateByTemplate_step'),
                       url(r'^scenario/create/(?P<step>.+)/$', scenarioCreateByTemplate, name='ts_ScenarioCreateByTemplate_step'),

                       url(r'^scenario/browse/$', ScenarioBrowseView.as_view(), name='ts_emod_scenario_browse'),
                       url(r'^scenario/browse/(?P<folder_id>[-\d]+)/$', ScenarioBrowseView.as_view(), name='ts_emod_scenario_browse'),
                       url(r'^scenario/browse_public/$', ScenarioBrowsePublicView.as_view(), name='ts_emod_scenario_browse_public'),
                       url(r'^scenario/details/(?P<scenario_id>\d+)/$', ScenarioDetailView.as_view(),
                           name='ts_emod_scenario_details'),
                       url(r'^scenario/delete/(?P<scenario_id>\d+)/$',
                           'ScenarioBrowseView.delete_scenario',
                           name='ts_emod_delete_scenario'),
                       url(r'^scenario/(?P<scenario_id>\d+)/run/delete/(?P<run_id>\d+)/$',
                           'ScenarioBrowseView.delete_run', name='ts_emod_scenario_run_delete'),
                       url(r'^scenario/duplicate/(?P<scenario_id>\d+)/$',
                           'ScenarioBrowseView.duplicate_scenario',
                           name='ts_emod_duplicate_scenario'),

                       url(r'^scenario/duplicate_run/(?P<run_id>\d+)/$',
                           'ScenarioBrowseView.run_to_scenario',
                           name='ts_emod_run_to_scenario'),

                       url(r'^scenario/approve/(?P<scenario_id>\d+)/$',
                           'ScenarioDetailView.approve_scenario',
                           name='ts_emod_approve_scenario'),

                       url(r'^scenario/(?P<step>.+)/intervention/(?P<intervention_id>[-\d]+)/$', baseline_wizard,
                           name='ts_scenario_step'),

                       url(r'^scenario/location/feedback/$', 'LocationView.getLocationGraphs',
                           name='ts_emod_location_graphs'),
                       url(r'^scenario/location/feedback/(?P<location_id>[\w]+)/$',
                           'LocationView.getLocationGraphs', name='ts_emod_location_graphs'),

                       url(r'^scenario/reset/$', 'BaselineWizardView.reset_scenario', name='ts_emod_scenario_reset'),
                       url(r'^scenario/cancel/$', 'BaselineWizardView.cancel_edit',
                           name='ts_emod_scenario_cancel_edit'),

                       url(r'^scenario/(?P<step>.+)/species/(?P<species_id>[-\d]+)/$', baseline_wizard,
                           name='ts_scenario_step'),
                       url(r'^scenario/species/delete/(?P<species_id>\d+)/$', 'SpeciesView.deleteSpecies',
                           name='ts_emod_species_delete'),
                       url(r'^scenario/species/save/$', 'SpeciesView.saveSpecies', name='ts_emod_species_save'),
                       url(r'^scenario/species/form/$', 'SpeciesView.getFormSpecies',
                           name='ts_emod_species_create_form'),
                       url(r'^scenario/species/form/(?P<species_name>[\w.]+)/$', 'SpeciesView.getFormSpecies',
                           name='ts_emod_species_create_form'),

                       url(r'^scenario/(?P<step>.+)/(?P<scenario_id>[-\d]+)/$', baseline_wizard,
                           name='ts_scenario_step'),
                       url(r'^scenario/(?P<step>.+)/$', baseline_wizard, name='ts_scenario_step'),
                       url(r'^scenario/$', baseline_wizard, name='ts_scenario_step'),

                       url(r'download/type/(?P<file_type>[\w]+)/$', download_view, name='ts_emod_download'),

                       url(r'^edit/$', JsonEditView.as_view(), name='ts_emod_json_edit'),
                       url(r'^edit/(?P<scenario_id>.+)/(?P<file_type>[\w.]+)$', JsonEditView.as_view(), name='ts_emod_json_edit'),

                       url(r'^scenario/chart/$', 'BaselineWizardView.get_chart',
                           name='ts_emod_scenario_bin_chart'),
                       url(r'^scenario/chart/(?P<scenario_id>\d+)/(?P<file_type>[\w.]+)$', 'BaselineWizardView.get_chart',
                           name='ts_emod_scenario_bin_chart'),

                       # Add new scenario edit wizard
                       url(r'^edit/(?P<step>.+)/(?P<scenario_id>[-\d]+)/$', edit_wizard,
                           name='ts_edit_step'),
                       url(r'^edit/(?P<step>.+)/$', edit_wizard, name='ts_edit_step'),
                       url(r'^edit/$', edit_wizard, name='ts_edit_step'),
                       url(r'^edit/(?P<step>.+)/species/(?P<species_id>[-\d]+)/$', edit_wizard,
                           name='ts_edit_step'),
                       ##################  Run  ##################
                       url(r'^run/duplicate/(?P<run_id>\d+)/$', 'RunDetailView.duplicateRun',
                           name='ts_emod_duplicate_run'),

                       url(r'^simulation/details/run/(?P<run_id>\d+)/$', RunDetailView.as_view(),
                           name='ts_emod_run_details'),
                       url(r'^simulation/metadata/run/(?P<run_id>\d+)/$', RunMetadataDetailView.as_view(),
                           name='ts_emod_run_metadata_details'),
                       url(r'^simulation/metadata/run/(?P<run_id>\d+)/(?P<mode>[\w]+)/$', RunMetadataDetailView.as_view(),
                           name='ts_emod_run_metadata_details'),

                       url(r'^run/location/feedback/$', 'LocationView.getLocationGraphs',
                           name='ts_emod_location_graphs'),
                       url(r'^run/location/feedback/(?P<location_id>[\w]+)/$', 'LocationView.getLocationGraphs',
                           name='ts_emod_location_graphs'),


                       url(r'^run/species/delete/(?P<species_id>\d+)/$', 'SpeciesView.deleteSpecies',
                           name='ts_emod_species_delete'),
                       url(r'^run/species/save/$', 'SpeciesView.saveSpecies', name='ts_emod_species_save'),
                       url(r'^run/species/form/$', 'SpeciesView.getFormSpecies', name='ts_emod_species_create_form'),
                       url(r'^run/species/form/(?P<species_name>[\w.]+)/$', 'SpeciesView.getFormSpecies',
                           name='ts_emod_species_create_form'),

                       url(r'^template/(?P<template_id>\d+)/$', TemplateDetailView.as_view(),
                           name='ts_emod_template_details'),

                       url(r'upload/type/(?P<file_type>[\w]+)/$', upload_view, name='ts_emod_upload'),
                       url(r'upload/$', upload_view, name='ts_emod_upload'),

                       url(r'^utilities/$', TemplateView.as_view(template_name="ts_emod/utilities.html"), name="ts_emod.utilities"),

                       # Results Viewer
                       url(r'^results_viewer/$', ResultView.as_view(), name='results_viewer.index'),
                       url(r'^results_viewer/scenario/(?P<scenario_id>\d+)/$', ResultByScenarioView.as_view(), name='results_viewer.scenario'),
                       url(r'^results_viewer/run/(?P<run_id>\d+)/$', ResultByRunView.as_view(), name='results_viewer.run'),

                        #
                       url(r'^csv_download/(?P<dim_run_id>\d+)/$', download_csv_file, name="ts_emod.csv_download")
                       )
