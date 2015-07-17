from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

from views import IndexView
from views import ScenarioListView, ScenarioValidationView, ScenarioStartView, ScenarioMonitoringView, \
    ScenarioSummaryView
from views import ScenarioDemographyView, ScenarioHealthSystemView, ScenarioSubmitView, ScenarioDeleteView, \
    duplicate_scenario
from views import ExperimentUploadView, ExperimentValidateView, ExperimentRunView
from views import StandaloneSubmitView, ScenarioEntomologyView, ScenarioInterventionsView, ScenarioDeploymentsView
from views.ExperimentRunView import get_sim_group_status, download_experiment_zip
from views.ScenarioView import download_scenario, download_experiment_scenario, save_scenario, submit_scenarios
from views.ScenarioMonitoringView import update_monitoring_form
from views.ScenarioDemographyView import update_demography_form
from views.ScenarioHealthSystemView import update_healthsystem_form
from views.ScenarioEntomologyView import update_entomology_form
from views.ScenarioInterventionsView import update_interventions_form

urlpatterns = patterns('',
                       url(r'^$', IndexView.as_view(), name='ts_om.index'),
                       url(r'^list/$', login_required(ScenarioListView.as_view()), name='ts_om.list'),
                       url(r'^experiment/upload/$', login_required(ExperimentUploadView.as_view()),
                           name='ts_om.upload'),
                       url(r'^experiment/validate/$', ExperimentValidateView.as_view(), name='ts_om.validate'),
                       url(r'^(?P<experiment_id>.+)/experiment/run/(?P<run_type>\w+)/$', ExperimentRunView.as_view(),
                           name='ts_om.run'),
                       url(r'^(?P<experiment_id>.+)/experiment/download/(?P<run_type>\w+)/$', download_experiment_zip,
                           name='ts_om.download_experiment'),
                       url(r'^(?P<scenario_id>.+)/experiment/(?P<index>.+)/scenario/download/$', download_experiment_scenario,
                           name='ts_om.download_experiment_scenario'),
                       url(r'^restValidate/$', ScenarioValidationView.as_view(), name='ts_om.restValidate'),
                       url(r'^start/$', login_required(ScenarioStartView.as_view()), name='ts_om.start'),
                       url(r'^(?P<scenario_id>.+)/monitoring/$', ScenarioMonitoringView.as_view(), name='ts_om.monitoring'),
                       url(r'^(?P<scenario_id>.+)/demography/$', ScenarioDemographyView.as_view(), name='ts_om.demography'),
                       url(r'^(?P<scenario_id>.+)/healthsystem/$', ScenarioHealthSystemView.as_view(),
                           name='ts_om.healthsystem'),
                       url(r'^(?P<scenario_id>.+)/entomology/$', ScenarioEntomologyView.as_view(), name='ts_om.entomology'),
                       url(r'^(?P<scenario_id>.+)/interventions/$', ScenarioInterventionsView.as_view(),
                           name='ts_om.interventions'),
                       url(r'^(?P<scenario_id>.+)/deployments/$', ScenarioDeploymentsView.as_view(), name='ts_om.deployments'),
                       url(r'^(?P<scenario_id>.+)/summary/$', ScenarioSummaryView.as_view(), name='ts_om.summary'),
                       url(r'^submitScenario/$', ScenarioSubmitView.as_view(), name='ts_om.submitScenario'),
                       url(r'^deleteScenario/$', ScenarioDeleteView.as_view(), name='ts_om.deleteScenario'),
                       url(r'^(?P<scenario_id>.+)/duplicate/$', duplicate_scenario, name='ts_om.duplicate'),
                       url(r'^(?P<scenario_id>.+)/download/$', download_scenario, name='ts_om.download'),
                       url(r'^(?P<scenario_id>.+)/save/$', save_scenario, name='ts_om.save'),
                       url(r'^scenarios/submit/$', submit_scenarios, name='ts_om.submit'),
                       url(r'^submit/$', StandaloneSubmitView.as_view(), name="ts_om.standalone_submit"),
                       url(r'^utilities/$', TemplateView.as_view(template_name="ts_om/utilities.html"),
                           name='ts_om.utilities'),
                       url(r'^(?P<experiment_id>.+)/experiment/run/(?P<run_type>\w+)/status/$', get_sim_group_status,
                           name='ts_om.run_status'),
                       url(r'^(?P<scenario_id>.+)/monitoring/update/form/$', update_monitoring_form,
                           name='ts_om.monitoring.update.form'),
                       url(r'^(?P<scenario_id>.+)/demography/update/form/$', update_demography_form,
                           name='ts_om.demography.update.form'),
                       url(r'^(?P<scenario_id>.+)/healthsystem/update/form/$', update_healthsystem_form,
                           name='ts_om.healthsystem.update.form'),
                       url(r'^(?P<scenario_id>.+)/entomology/update/form/$', update_entomology_form,
                           name='ts_om.entomology.update.form'),
                       url(r'^(?P<scenario_id>.+)/interventions/update/form/$', update_interventions_form,
                           name='ts_om.interventions.update.form'),
                       )
