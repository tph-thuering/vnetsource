from django.conf.urls import include, patterns, url

# from data_services.views.inputFile import inputFile
from data_services.views.geojson import GeoJsonView
from data_services.views.misc_functions import update_emod_config, send_calibration_request_ajax
from .rest_api.api import v1_api
from data_services.views import publicize_scenario
from data_services.views.views import update_names_and_organizations_in_dim_run_table
from data_services.views.manifestview import ManifestView
from data_services.views.metadataview import MetadataView


urlpatterns = patterns('data_services.views',

    # Is it still being used?
    # If not it should be deleted, as well as a reference to datawarehouse.view.JSONMixin
    url(r'^geo', GeoJsonView.as_view(), name='geojson_view'),
    (r'^api/', include(v1_api.urls)),
    # For ts_emod - make specified scenario public
    url(r'^publicize_scenario/(?P<baseline_id>\d+)/$', 'publicize_scenario.publicize_scenario', name='publicize_scenario'),
    # Returns manifest file for specified run. Used by cluster scripts
    url(r'^manifest/(?P<runID>\d+)$', ManifestView.as_view(), name='datawarehouse_manifest'),
    # Update names and organizations in DimRun model
    url(r'^update_names_and_organizations_in_dim_run_table/$', update_names_and_organizations_in_dim_run_table,
        name="update_names_and_organizations_in_dim_run_table"),
    # return JSON of metadata for all public runs 
    url(r'^metadata/$', MetadataView.as_view(), name='datawarehouse_metadata'),
    # return JSON of metadata for a run 
    url(r'^metadata/(?P<runID>\d+)$', MetadataView.as_view(), name='datawarehouse_metadata'),
    # Depricated, should be removed after Risk Mapper is switched to manifest-based runs
    # url(r'^inputFile/(?P<rep_id>\d+)/(?P<file_type>\S+)', inputFile.as_view(), name='datawarehouse_input_files'),

    url(r'^api/update_emod_config/(?P<scenario_id>\d+)/$', update_emod_config, name='data_services.update_emod_config'),
    url(r'^api/send_calibration_request/(?P<scenario_id>\d+)/$', send_calibration_request_ajax, name='data_services.send_calibration_request'),
)