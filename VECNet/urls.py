########################################################################################################################
# VECNet CI - Prototype
# Date: 4/5/2013
# Institution: University of Notre Dame
# Primary Authors:
########################################################################################################################
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf import settings
from lib.views.RevisionView import RevisionView
from django.views.generic.base import RedirectView

# Uncomment the next two lines to enable the admin:
admin.autodiscover()

urlpatterns = patterns('',

    url(r'^admin/', include(admin.site.urls)),
    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    #Included App URLs

    url(r'^$', include('lib.urls')),
    #url(r'^expert_emod/', include('expert_emod.urls')), made obsolete by ts_emod
    url(r'^datawarehouse/', include('datawarehouse.urls')),
    url(r'^ts/', include('transmission_simulator.urls')),
    url(r'^ts_emod/', include('ts_emod.urls')),
    url(r'^accounts/login/', 'django.contrib.auth.views.login', {'template_name': 'admin/login.html'},
        name="auth_login"),
    url(r'^accounts/logout/', 'django.contrib.auth.views.logout', name="auth_logout"),
    #url(r'^login/', RedirectView.as_view(url=s ettings.LOGIN_URL), name="auth_login"),
    url(r'^autoscotty/', include('autoscotty.urls')),
    url(r'^data_services/', include('data_services.urls')),
    url(r'^revision$', RevisionView.as_view()),
    url(r'^ts_weather/', include('ts_weather.urls')),
    url(r'^ts_om_viz/', include('ts_om_viz.urls')),
    url(r'^ts_get_started/', include('ts_get_started.urls')),

    # error page URLS
    url(r'^500$', 'lib.views.error_views.view_server_error', name="error_template_500"),
    url(r'^403$', 'lib.views.error_views.view_server_error', {'template_name': '403.html'}, name="error_template_403"),
    url(r'^404$', 'lib.views.error_views.view_server_error', {'template_name': '404.html'}, name="error_template_404"),
    url(r'^error_submit$', 'lib.views.error_views.error_submit', name="submit_server_error"),
    url(r'^job_services/', include('job_services.urls')),
    url(r'^results_viewer/', include('results_visualizer.urls')),
    url(r'^ts_om/', include('ts_om.urls')),
    url(r'^om_validate/', include('om_validate.urls')),
    url(r'^ts_repr/', include('ts_repr.urls')),
    url(r'^ts_emod2/', include('ts_emod2.urls'))
)

try:
    from .urls_local import urlpatterns_local
    urlpatterns += urlpatterns_local
except ImportError:
    pass

handler500 = 'lib.views.error_views.view_server_error'