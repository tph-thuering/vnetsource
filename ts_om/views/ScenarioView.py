from StringIO import StringIO
import json
import zipfile

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.views.generic import View
from lxml import etree
from lxml.etree import XMLSyntaxError

from ts_om.models import Scenario, ExperimentFile
from ts_om.submit import submit
from ts_om.views.ScenarioValidationView import rest_validate

__author__ = 'nreed'


class ScenarioView(View):
    pass


def duplicate_scenario(request, scenario_id):
    if not request.user.is_authenticated() or not scenario_id or scenario_id < 0:
        return

    scenario = Scenario.objects.get(user=request.user, id=int(scenario_id))

    if not scenario:
        return

    xml = scenario.xml

    try:
        tree = etree.parse(StringIO(str(xml)))
    except XMLSyntaxError:
        return
    else:
        tree.getroot().set('name', scenario.name + " (duplicate)")
        xml = etree.tostring(tree.getroot(), encoding='UTF-8')

    new_scenario = Scenario.objects.create(xml=xml, start_date=scenario.start_date, user=request.user)
    new_scenario.save()

    return HttpResponseRedirect(reverse('ts_om.summary', kwargs={'scenario_id': new_scenario.id}))


def download_scenario(request, scenario_id):
    if not request.user.is_authenticated() or not scenario_id or scenario_id < 0:
        return

    scenario = Scenario.objects.get(user=request.user, id=int(scenario_id))

    if not scenario:
        return

    f = StringIO(str(scenario.xml))
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(f, parser)
    xml = etree.tostring(tree.getroot(), encoding='UTF-8', pretty_print=True)

    return HttpResponse(xml)


def download_experiment_scenario(request, scenario_id, index):
    scenario_id = int(scenario_id)
    index = int(index)
    xml = ""

    if not request.user.is_authenticated() or not scenario_id or scenario_id < 0:
        return

    experiment = ExperimentFile.objects.get(user=request.user, id=int(scenario_id))

    if not experiment:
        return

    experiment_file = experiment.file
    proj_path = getattr(settings, "PROJECT_PATH", None)
    full_path = proj_path + experiment_file.url

    if zipfile.is_zipfile(experiment_file):
        exp_zip = zipfile.ZipFile(full_path)
        name_lst = exp_zip.namelist()

        n = [name for name in name_lst if name.endswith(".xml")][index]
        with exp_zip.open(n) as exp_file:
            xml = exp_file.read()
    else:
        if experiment_file.url.endswith(".xml"):
            xml = experiment_file.read()

    return HttpResponse(xml, content_type="text/xml")


def save_scenario(request, scenario_id):
    if not request.user.is_authenticated() or not scenario_id or scenario_id < 0:
        return

    xml_file = request.read()
    json_str = rest_validate(xml_file)
    validation_result = json.loads(json_str)

    valid = True if (validation_result['result'] == 0) else False

    if not valid:
        return HttpResponse(json_str, content_type="application/json")

    scenario = Scenario.objects.get(user=request.user, id=int(scenario_id))

    if not scenario:
        return HttpResponse({'saved': False}, content_type="application/json")

    scenario.xml = xml_file
    scenario.save()

    return HttpResponse(json.dumps({'saved': True}), content_type="application/json")


def submit_scenarios(request):
    scenarios_data = {"ok": False, "scenarios": []}

    if not request.user.is_authenticated() or not "scenario_ids" in request.POST:
        return HttpResponse(json.dumps(scenarios_data), content_type="application/json")

    scenario_ids = json.loads(request.POST["scenario_ids"])

    if scenario_ids is None or len(scenario_ids) <= 0:
        return HttpResponse(json.dumps(scenarios_data), content_type="application/json")

    for scenario_id in scenario_ids:
        scenarios_data["scenarios"].append({"id": scenario_id, "ok": False})

        scenario = Scenario.objects.get(user=request.user, id=int(scenario_id))

        if not scenario or scenario.simulation is not None:
            continue

        json_str = rest_validate(scenario.xml)
        validation_result = json.loads(json_str)

        valid = True if (validation_result['result'] == 0) else False

        if not valid:
            continue

        simulation = submit(request.user.username, scenario.xml)

        if simulation:
            scenario.simulation = simulation
            scenario.save()
            scenarios_data["scenarios"][-1]["ok"] = True

    scenarios_data["ok"] = True

    return HttpResponse(json.dumps(scenarios_data), content_type="application/json")
