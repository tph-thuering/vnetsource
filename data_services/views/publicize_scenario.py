from django.core.exceptions import ObjectDoesNotExist
from data_services.models import DimBaseline
from django.http import Http404
from django.shortcuts import redirect
from lib.templatetags.base_extras import set_notification


def publicize_scenario(request, baseline_id):
    try:
        scenario = DimBaseline.objects.get(id=baseline_id)
        scenario.is_public = True
        scenario.save()

    except ObjectDoesNotExist:
        raise Http404('Scenario with id %s does not exist.' % baseline_id)

    set_notification('alert-success', '<strong>Success!</strong> You have successfully made simulation public'
                     , request.session)

    return redirect("ts_emod_scenario_details", scenario_id=baseline_id)


def privatize_scenario(request, baseline_id):
    try:
        scenario = DimBaseline.objects.get(id=baseline_id)
        scenario.is_public = False
        scenario.save()
    except ObjectDoesNotExist:
        raise Http404('Scenario with id %s does not exist.' % baseline_id)

    set_notification('alert-success', '<strong>Success!</strong> You have successfully made simulation private'
                     , request.session)

    return redirect("ts_emod_scenario_details", scenario_id=baseline_id)