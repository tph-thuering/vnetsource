########################################################################################################################
# VECNet CI - Prototype
# Date: 03/21/2014
# Institution: University of Notre Dame
# Primary Authors:
#   Robert Jones <Robert.Jones.428@nd.edu>
########################################################################################################################

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseBadRequest
from lib.templatetags.base_extras import set_notification

def download_view(request, file_type=None):
    """
    ## View for file downloads ##
      - Given a file_type, return the file of that type from the scenario in the session.

     filetypes = [
            'air binary',
            'air json',
            'humidity binary',
            'humidity json',
            'land_temp binary',
            'land_temp json',
            'rainfall binary',
            'rainfall json',
            'config',
            'campaign',
            'demographics',
        ]
    """

    if file_type is None:
        return HttpResponseBadRequest('No file selected for download.')
    if 'scenario' not in request.session.keys():
        return HttpResponseBadRequest('No scenario selected to download from.')

    try:
        my_file = request.session['scenario'].get_file_by_type(file_type)
    except ObjectDoesNotExist:
        set_notification('alert-error', '<strong>Error!</strong> File does not exist.', request.session)
        return HttpResponseBadRequest('Scenario does not contain a file of this type.')

    response = HttpResponse(mimetype='text/plain')
    response['Content-Disposition'] = 'attachment; filename="%s"' % my_file.file_name
    response.write(my_file.content)

    return response