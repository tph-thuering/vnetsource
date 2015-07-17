from django.conf.urls import patterns, url
from ts_get_started import views
from django.views.generic import TemplateView

urlpatterns = patterns('',
    url(r'^$', views.IndexView.as_view(), name='ts_get_started_index'),
    url(r'^modeling1/$', views.Modeling1View.as_view(), name='ts_get_started_modeling1'),
    url(r'^modeling2/$', views.Modeling2View.as_view(), name='ts_get_started_modeling2'),
    url(r'^modeling3/$', views.Modeling3View.as_view(), name='ts_get_started_modeling3'),
    url(r'^modeling4/$', views.Modeling4View.as_view(), name='ts_get_started_modeling4'),
    url(r'^weatherGenerator/$', views.WeatherGeneratorView.as_view(), name='ts_get_started_weatherGenerator'),
    url(r'^select_model/$', TemplateView.as_view(template_name="ts_get_started/frank_index.html"), name="ts_get_started.frank.index"),
    url(r'^emod_model/$', TemplateView.as_view(template_name="ts_get_started/frank_emod.html"), name="ts_get_started.frank.emod"),
    url(r'^emod_single_node/$', TemplateView.as_view(template_name="ts_get_started/frank_single_node.html"), name="ts_get_started.frank.emod_single_node"),
    url(r'^temperatureData/$', views.getTemperatureData, name='ts_weather.temperatureData'),
    url(r'^rainfallData/$', views.getRainfallData, name='ts_weather.rainfallData'),
    url(r'^humidityData/$', views.getHumidityData, name='ts_weather.humidityData'),
)