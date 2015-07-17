from collections import OrderedDict
from django.http import HttpResponse
import simplejson


class JSONMixin(object):
    """This class was designed to be inherited and used to return JSON objects from an Ordered Dictionary
    """
    ## Ordered Dictionary used to create serialized JSON object
    # return_rderedDict() #This will enforce the ordering that we recieve from the database

    def __init__(self):
        """
        Init function for the JSON Mixin class
        """
        self.return_list=OrderedDict()

        return

    def render_to_response(self, context):
        """Extends default render to response to return serialized JSON.
        """
        return self.get_json_response(self.convert_to_json())

    def get_json_response(self, content, **httpresponse_kwargs):
        """Returns JSON to calling object in the form of an http response.
        """
        return HttpResponse(content,content_type='application/json',**httpresponse_kwargs)

    def convert_to_json(self):
        """Serialized the return_list into JSON
        """
        return simplejson.dumps(self.return_list)