# #######################################################################################################################
# VECNet CI - Prototype
# Date: 4/5/2013
# Institution: University of Notre Dame
# Primary Authors:
########################################################################################################################
from django.conf.urls import patterns, url
from autoscotty.views import UploadZip, ReportError


urlpatterns = patterns('datawarehouse.views',
                       url(r'^$', UploadZip.as_view(), name='autoscotty_upload'),
                       url(r'report', ReportError.as_view(), name='autoscotty_report'),
)
