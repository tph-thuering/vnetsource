from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from data_services.models import DimUser

from lib.templatetags.base_extras import set_notification

from ts_emod2.models import Scenario

import json
import datetime


@csrf_exempt
def copy_scenario(request, scenario_id):
    old_scenario = Scenario.objects.get(id=scenario_id)

    include_output = json.loads(request.POST['include_output'])
    should_link_experiment = json.loads(request.POST['should_link_experiment'])
    should_link_simulation = json.loads(request.POST['should_link_simulation'])
    should_link_simulation_files = json.loads(request.POST['should_link_simulation_files'])

    new_scenario = old_scenario.copy(include_output, should_link_experiment, should_link_simulation, should_link_simulation_files)

    goto_url = reverse("ts_emod2.details", kwargs={'scenario_id': new_scenario.id})

    set_notification('alert-success', '<strong>Success!</strong> Simulation copied.', request.session)

    return HttpResponse(content=goto_url)


@csrf_exempt
def delete_scenarios(request):
    dim_user = DimUser.objects.get(username=request.user.username)
    number_of_scenarios_deleted = 0
    number_of_scenarios_denied = 0

    if 'scenarios' in request.POST:
        scenarios_to_delete = json.loads(request.POST['scenarios'])
        for i in range(len(scenarios_to_delete)):
            try:
                delete_scenario(dim_user, scenarios_to_delete[i])
                number_of_scenarios_deleted += 1
            except PermissionDenied:
                number_of_scenarios_denied += 1

        if number_of_scenarios_deleted > 0:
            set_notification('alert-success', '<strong>Success!</strong> Successfully deleted ' + str(number_of_scenarios_deleted) + ' scenario(s).', request.session)
        if number_of_scenarios_denied > 0:
            set_notification('alert-error', '<strong>Error!</strong> ' + str(number_of_scenarios_denied) + ' scenario(s) do not belong to you and were not deleted. ', request.session)
    else:
        set_notification('alert-error', '<strong>Error!</strong> No scenarios were deleted. Scenario ids were missing in the post request. ', request.session)

    return HttpResponse()


def delete_scenario(dim_user, scenario_id):
    scenario = Scenario.objects.get(id=scenario_id)

    if scenario.user != dim_user:
        raise PermissionDenied

    scenario.deletion_timestamp = datetime.datetime.now()
    scenario.save()