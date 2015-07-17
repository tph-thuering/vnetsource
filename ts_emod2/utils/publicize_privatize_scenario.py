from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import redirect

from lib.templatetags.base_extras import set_notification

from ts_emod2.models import Scenario


def publicize_scenario(request, scenario_id):
    try:
        scenario = Scenario.objects.get(id=scenario_id)
        scenario.is_public = True
        scenario.save()

    except ObjectDoesNotExist:
        raise Http404('Scenario with id %s does not exist.' % scenario_id)

    set_notification('alert-success',
                     '<strong>Success!</strong> You have successfully made the simulation public.',
                     request.session)

    return redirect("ts_emod2.details", scenario_id=scenario_id)


def privatize_scenario(request, scenario_id):
    try:
        scenario = Scenario.objects.get(id=scenario_id)
        scenario.is_public = False
        scenario.save()
    except ObjectDoesNotExist:
        raise Http404('Scenario with id %s does not exist.' % scenario_id)

    set_notification('alert-success',
                     '<strong>Success!</strong> You have successfully made the simulation private.',
                     request.session)

    return redirect("ts_emod2.details", scenario_id=scenario_id)