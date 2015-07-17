########################################################################################################################
# VECNet CI - Prototype
# Date: 10/14/2013
# Institution: University of Notre Dame
# Primary Authors:
#   Robert Jones <Robert.Jones.428@nd.edu>
########################################################################################################################
# import the django settings
#from django.conf import settings
# for HTTP response
from django.http import HttpResponseBadRequest  # HttpResponse,
from django.shortcuts import render_to_response, redirect
# for loading template
from django.template import RequestContext
from lib.templatetags.base_extras import set_notification

# for generating json
import json

# for os manipulations
#import os
# used to generate random unique id
#import uuid

from ts_emod.views.BaselineWizardView import baseline_wizard
from ts_emod.views.InterventionToolView import intervention_tool


def upload_view(request, file_type=None):
    """
    ## View for file uploads ##

    It does the following actions:
    - displays a template if no action has been specified
    - read in a file into session variables
            allowed filetypes = [
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

    if request.method != 'POST':
        # GET
        return render_to_response("ts_emod/upload.html", {},
                                  context_instance=RequestContext(request))
    else:
        # POST request
        # user has triggered an upload action
        if not request.FILES:
            return HttpResponseBadRequest('Please select a ' + file_type + ' file.')  # type is probably empty

        if request.POST.get("calling_page") == 'ts_intervention_tool_step':
            redirect_url = intervention_tool
        # else:
        #     redirect_url = scenario_wizard

        # get the uploaded file
        my_file = request.FILES[u'file']
        file_contents = request.FILES.get('file').read()

        if file_type in ('air json', 'humidity json', 'land_temp json', 'rainfall json', 'config', 'campaign',
                         'demographics'):
            try:
                json.loads(file_contents)
            except ValueError:
                return HttpResponseBadRequest('Please select a file in JSON format.')

        if file_type in 'demographics':
            # check validity of file
            if 'IndividualAttributes' not in file_contents:
                return HttpResponseBadRequest('Please select a demographic file (in JSON format).')
            redirect_url = baseline_wizard
            redirect_step = "demographic"

        elif file_type in 'campaign':

            # check for valid campaign file
            if 'Events' not in file_contents:
                return HttpResponseBadRequest('Please select a campaign.json file.')

            # insert file/contents into session for use in intervention step
            request.session['uploaded_file_campaign_name'] = my_file.name
            request.session['uploaded_file_campaign'] = json.loads(file_contents)
            redirect_step = "intervention"

        if redirect_url == baseline_wizard and 'scenario' in request.session.keys():
            # add_file_from_string(self, file_type, name, content, description=None):
            request.session['scenario'].add_file_from_string(file_type, my_file.name,
                                                             str(file_contents),
                                                             description=file_type)
            request.session['scenario'].save()

        set_notification('alert-success', '<strong>Success!</strong> You have successfully uploaded the file '
                         + my_file.name + '.', request.session)
        #return redirect(redirect_url, step=redirect_step)
        if redirect_url == intervention_tool:
            kwargs = {"scenario_id": str(request.session['scenario'].id)}

        return redirect(redirect_url, step="intervention", **kwargs)