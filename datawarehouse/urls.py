########################################################################################################################
# VECNet CI - Prototype
# Date: 4/5/2013
# Institution: University of Notre Dame
# Primary Authors:
########################################################################################################################
from django.conf.urls import patterns, url, include
from datawarehouse.views.IndexView import IndexView
from datawarehouse.views.CubeResultsView import CubeResultsView
from datawarehouse.views.SliceBrowser import SliceBrowser
from datawarehouse.views.LookUpResults import LookUpResults
from datawarehouse.views.LookUpResultsJSON import LookUpResultsJSON
from datawarehouse.views.CubeView import CubeView
from api import Lookup
from forms.ETLForms import upload_wizard_view
from views.IngestionView import IngestionView
from django.views.decorators.csrf import csrf_exempt

urlpatterns = patterns('datawarehouse.views',
    # Index view
    url(r'^$', IndexView.as_view(), name='datawarehouse_index'),

    # Datawarehouse browser - Larry
    url(r'^api/', include(Lookup.urls)),
    url(r'LookUpTable',LookUpResults.as_view(), name='datawarehouse_lookUpResults'),
    url(r'lookuptable',csrf_exempt(LookUpResultsJSON().process_table_data), name='datawarehouse_lookUpResults2'),
    url(r'simpleparam',csrf_exempt(LookUpResultsJSON().process_table_data_simple), name='datawarehouse_lookUpResults3'),
    #url(r'MLookUpTable1',LookUpResultsJSON().test, name='datawarehouse_lookUpResults4'),
    url(r'alltables',csrf_exempt(LookUpResultsJSON().test), name='datawarehouse_lookUpResults4'),
    url(r'SliceBrowser',SliceBrowser.as_view(),name='datawarehouse_sliceBrowser'),
    url(r'^cube$', CubeView.as_view(test=False), name='datawarehouse_cube'),
    url(r'^results/$', CubeResultsView.as_view(), name='datawarehouse_cube_results'),

    # ETL - Zach
    url(r'^etl/(?P<step>.+)$', upload_wizard_view, name='datawarehouse_etl'),
    url(r'^ingestion$', IngestionView.as_view(), name='datawarehouse_ingestion'),
)
