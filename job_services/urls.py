from django.conf.urls import patterns, url
from .views import CreateQuota, DeleteQuota, ListQuotas, UpdateQuota


urlpatterns = patterns('',
                       url(r'^quotas/$', ListQuotas.as_view(), name='list_quotas'),
                       url(r'^quota/(?P<pk>[\w-]+)$', UpdateQuota.as_view(), name='update_quota'),
                       url(r'^new/quota/$', CreateQuota.as_view(), name='create_quota'),
                       url(r'^delete/quota/(?P<pk>[\w-]+)$', DeleteQuota.as_view(), name='delete_quota'),
                       )
