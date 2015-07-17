########################################################################################################################
# VECNet CI - Prototype
# Date: 09/13/2013
# Institution: University of Notre Dame
# Primary Authors: Robert Jones <Robert.Jones.428@nd.edu>
########################################################################################################################

# Imports that are external to the ts_emod app
from data_services.adapters.EMOD import EMOD_Adapter
from django.http import HttpResponse
import json

def getLocationGraphs(request, location_id=None):
    """
    Function to get graph data from DW by url
     - Input: location ID
     - Output: JSON object of highchart data
     - if called without location ID, returns empty dict
    """
    if location_id == None:
        chart_dict = {}
    else:
        adapter = EMOD_Adapter()
        location_dict = adapter.fetch_locations()
        # get HighChart data object
        try:
            chart_dict = adapter.fetch_weather_chart(location_id, 'chart-div',
                                            start_date=location_dict[int(location_id)]['start_date'],
                                            end_date=location_dict[int(location_id)]['end_date'])
        except:
            chart_dict = {}
    return HttpResponse(json.dumps(chart_dict), mimetype="application/json")