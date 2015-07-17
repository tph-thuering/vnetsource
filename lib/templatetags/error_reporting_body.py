########################################################################################################################
# VECNet CI - Prototype
# Date: 10/07/2013
# Institution: University of Notre Dame
# Primary Authors: Caleb Reinking
########################################################################################################################
from django import template

register = template.Library()

@register.inclusion_tag('lib/tags/error_reporting_body.html', takes_context=False)
def error_reporting_body(error='500'):
    """
    This provides specific text for the server error pages so that the template tag can keep the design DRY

    :return: a dictionary of error details needed by the tag
    """
    dataDict = {}
    dataDict['error_code'] = error

    if( error == '500'):
        dataDict['error_explanation'] = "<strong>500 Internal Server Error!</strong> Something has gone wrong behind the scenes. An email has been sent to our development team with some details, \
                but it would help us fix the problem even speedier if you let us know how you encountered this problem."
    elif( error == '404'):
        dataDict['error_explanation'] = "<strong>404 Page Not Found!</strong> That's the technical way of letting you know that the page you were trying to reach can't be found. Please first check the page \
                address for typos. If the address looks good or you landed here by clicking on another link within our site, please let us \
                know by filling out the form below. We will work on correcting the issue as quickly as possible!"
    elif( error == '403'):
        dataDict['error_explanation'] = "<strong>403 Forbidden!</strong> Basically, that means that you aren't authorized to view this page. If you feel that you \
                should have access to the data requested, please let us know by filling out the form below. \
                We will work on correcting the issue as quickly as possible!"
    else:
        dataDict['error_explanation'] = "Unkown Error"

    dataDict['error_explanation'] += "<br/><br/>If you would rather not fill out the form to the left, you can head back to known \
                territory by using your browser's back button or by clicking on one of the links to the right."

    return dataDict
