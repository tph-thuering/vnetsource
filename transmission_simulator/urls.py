# PEP 0263
# -*- coding: utf-8 -*-
########################################################################################################################
# VECNet CI - Prototype
# Date: 4/5/2013
# Institution: University of Notre Dame
# Primary Authors:
#   Alexander Vyushkov <Alexander.Vyushkov@nd.edu>
########################################################################################################################

"""
URL dispatcher for the transmission simulator
"""

from django.conf.urls import patterns, url
from transmission_simulator.views import IndexView, BasicView, RepresentativeView

# URL dispatcher for the transmission simulator
urlpatterns = patterns('transmission_simulator.views',
                       # Main page for transmission simulator
                       url(r'^$', IndexView.as_view(), name='ts.index'),
                       url(r'^basic/$', BasicView.as_view(), name='ts.basic'),
                       url(r'^representative/$', RepresentativeView.as_view(), name='ts.representative'),
                    )