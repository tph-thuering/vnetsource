########################################################################################################################
# VECNet CI - Prototype
# Date: 4/5/2013
# Institution: University of Notre Dame
# Primary Authors:
#   Lawrence Selvy <Lawrence.Selvy.1@nd.edu>
#   Zachary Torstrick <Zachary.R.Torstrick.1@nd.edu>
########################################################################################################################

"""
Contains various tags for performing mathematical operations in Django templates.

It is often desireable to perform some mathematical operations in the HTML,
as opposed to on the server, in order to present things in an appealing way. Various
tags to assist with this are defined here.
"""

# import statements
from django import template

register = template.Library()

def getColumnDivisor(parser, token):
    """This is the compilation function for the getColumnDivisor tag.

    :param parser: The template parser
    :param token: The string used to call the template tag

    For example::

        {% getColumnDivisor mydict 3 %}
    """
    try:
        tag_name, var, cols = token.split_contents()    # split the contents of the tag into the tag name and variables
    except ValueError:                                  # if a variable wasn't found, raise an error
        raise template.TemplateSyntaxError("%r tag requires two arguments" % token.contents.split()[0])
    return GetColumnDivisor(var, cols)                  # render the variables using the custom renderer

class GetColumnDivisor(template.Node):
    """This is the custom renderer for the getColumnDivisor template tag.
    It extends Django's template.Node class. It expects a context variable
    such as a dictionary or list and an integer value. It adds to the
    context the number of items to display per column given the integer
    number of columns and the length of the object per column.
    """

    def __init__(self, var, cols):
        """The initialization method. Creates a template variable
        and an integer from the input.

        :param var: The list, dictionary, or tuple passed in from the tag
        :param cols: The number of desired columns
        """
        self.var = template.Variable(var)   # resolve the object using the context
        self.cols = int(cols)               # typecast the input string to an integer

    def render(self, context):
        """Responsible for rendering the content. Computes the length of
        the context object and uses this length in conjunction with
        the desired number of columns to determine the number of
        results per column.

        :param context: The page context.
        """
        varLen = len(self.var.resolve(context))     # get the object length
        try:                                        # compute the number of items per column
            if varLen%self.cols == 0:           
                content = varLen/self.cols
            else:
                content = varLen/self.cols+1
            context['column_divisor'] = content     # add items per column to the context
            return ''                                           
        except template.VariableDoesNotExist, template.TemplateSyntaxError:
            return 'Error rendering', self.variable
   
register.tag('getColumnDivisor', getColumnDivisor)  # register the function
