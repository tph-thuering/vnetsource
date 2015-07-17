from django.conf.urls import patterns, url
from ts_weather import views

urlpatterns = patterns('',
    url(r'^$', views.IndexView.as_view(), name='ts_weather.index'),
    url(r'^download$', views.DownloadView.as_view(), name='ts_weather.download'),
    url(r'^chartData/(?P<nodeID>\d+)/$', views.getChartData, name='ts_weather.chartData'),
    url(r'^getLocation/(?P<resolution>\d+.\d+\s+\w+)/$', views.getLocationFromDatabase, name='ts_weather.getLocation'),
    url(r'^addLocation/(?P<nodeID>\d+)/$', views.addLocationToDatabase, name='ts_weather.addLocation'),
    #url(r'^location/(?P<nodeID>\d+)/$', views.getLocation, name='ts_weather.location'),
    #url(r'^data/\d+/\d+/data/$', viewtastic_fetch_data, name="results_viewer_data"),
    #url(r'^csvDownload$', views.CsvDownloadView.as_view(), name='csvDownload'),
)

#     url(r'^a/$', 'a', name='a'),                      
#    #url(r'^$', views.index, name='index'),
#    url(r'^(?P<pk>\d+)/$', views.DetailView.as_view(), name='detail'),
#    url(r'^(?P<pk>\d+)/$', views.ResultsView.as_view(), name='results'),
#    #url(r'^(?P<poll_id>\d+)/$', views.detail, name='detail'),
#    #url(r'^(?P<poll_id>\d+)/results/$', views.results, name='results'),
#    url(r'^(?P<poll_id>\d+)/vote/$', views.vote, name='vote'),
#    url(r'^(?P<poll_id>\d+)/test/$', views.testView, name='test'),
