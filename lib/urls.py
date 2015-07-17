########################################################################################################################
# VECNet CI - Prototype
# Date: 4/5/2013
# Institution: University of Notre Dame
# Primary Authors:
########################################################################################################################
from django.conf.urls import patterns, url
from lib.views.IndexView import IndexView
urlpatterns = patterns('lib.views',
    url(r'^$', IndexView.as_view(), name='index'),
    )
