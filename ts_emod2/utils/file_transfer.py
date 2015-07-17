from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect

from data_services.models import DimUser
from lib.templatetags.base_extras import set_notification

import json
from ts_emod2.models import Scenario


def download(request, file_type, scenario_id):
    dim_user = DimUser.objects.get(username=request.user.username)
    scenario = Scenario.objects.get(id=scenario_id)

    the_file = scenario.get_file_by_type(file_type)

    #set_notification('alert-error', '<strong>Error!</strong> File does not exist.', request.session)
    #return HttpResponseBadRequest('Scenario does not contain a file of this type.')

    try:
        contents_as_json = json.loads(the_file.get_contents())
        formatted_contents = json.dumps(contents_as_json, indent=4, separators=(',', ': '))
    except:
        formatted_contents = the_file.get_contents()

    response = HttpResponse(content=formatted_contents, content_type='application/octet-stream')
    response['Content-Disposition'] = 'attachment; filename=' + scenario.get_filename_by_type(file_type)

    return response


def upload(request, file_type, scenario_id):
    dim_user = DimUser.objects.get(username=request.user.username)
    scenario = Scenario.objects.get(id=scenario_id)

    if scenario.user != dim_user:
        raise PermissionDenied

    set_notification('alert-success', '<strong>Success!</strong> Saved new json.', request.session)
    set_notification('alert-error', '<strong>Error!</strong> Failed to save json.', request.session)

    scenario.set_file_by_type(file_type, request.FILES[file_type].read())

    return redirect("ts_emod2.details", scenario_id=scenario_id)