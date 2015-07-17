########################################################################################################################
# VECNet CI - Prototype
# Date: 4/5/2013
# Institution: University of Notre Dame
# Primary Authors:
#   Robert Jones <Robert.Jones.428@nd.edu>
#   Gregory Davis <gdavis2@nd.edu>
########################################################################################################################

# Imports that are external to the expert_emod app

from django.db import models
from django import forms
from django import utils
from django.forms.util import flatatt
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _
from django.utils.html import escape
import json

class UnValidatedMultipleChoiceField(forms.MultipleChoiceField):
    """A class representing an extension of forms.MultipleChoiceField

    Does not validate if the field values are in self.choices
    Allows a multiple choice form input to be used in the Scenario "Intervention Shopping Cart" form as list input.

        - So that a list of values of each type is captured by the form:
        - All intervention ID's in one list, start_days in another, dist_durations in a third, etc.
        - All indexed in proper order: [0] index for each list gets values for intervention[0].

    Unvalidated because Validation of MultipleChoiceField interferes with this use.
    """

    def to_python(self, value):
        """Override checking method"""
        return value

    def validate(self, value):
        """This avoids default validation method
        """
        pass

class JSONEditableField(models.Field):
    """A class representing an extension of models.Field

    JSONEditableField type renders a JSON object as form inputs and brings the result input back as JSON.
    based on http://stackoverflow.com/questions/9541924/pseudo-form-in-django-admin-that-generates-a-json-object-on-save
    """
    description = _("JSON")

    def db_type(self, connection):
        """Method to return field type

        - this is required for syncdb to work (but also broke Django unit testing when set to charfield)

        :returns: text
        """
        return 'text'

    def formfield(self, **kwargs):
        """Method to override models.Field formfield

        Returns default formfield to return JSONEditableFormField
        """
        defaults = {'form_class': JSONEditableFormField}
        defaults.update(kwargs)
        return super(JSONEditableField, self).formfield(**defaults)

class JSONEditableWidget(forms.Widget):
    """A class representing an extension of forms.Widget

    A widget that handles formatting the data in a JSON object into form inputs.
    """
    def as_field(self, name, key, value):
        """A method that extends the widget to return input fields

        It takes a JSON key/value pair and renders as HTML label and input field
        """
        attrs = self.build_attrs(name="%s__%s" % (name, key))
        attrs['value'] = utils.encoding.force_unicode(value)
        key = key.replace('_', ' ')
        key = key.replace('CostToConsumer', 'Cost to Consumer')
        key = key.replace('rate', ' rate')
        return u'<div class="row"><div class="span2"><label>%s:</label></div><div class="span2"><input%s type="text"/></div></div>' % (key.capitalize(), forms.util.flatatt(attrs))

    def as_list(self, name, key, value):
        """A method that extends the widget to return input fields

        Takes a JSON key/value list pair and returns HTML label and drop-down selector field
        """
        attrs = self.build_attrs(name="%s__%s" % (name, key))
        #attrs['value'] = utils.encoding.force_unicode(value)
        my_options = '<option value="">Please select...</option>'
        for my_item in value:
            my_options = my_options + '<option value="'+my_item+'">'+my_item+'</option>'
        return u'<div class="row"><div class="span2"><label>%s:</label></div><div class="span2"><select %s >%s</select></div></div>' % (key.capitalize(), forms.util.flatatt(attrs), my_options)

    def to_fields(self, name, json_obj):
        """A method that extends the widget

        Get list of rendered fields for json object
        """
        inputs = []
        for key, value in sorted(json_obj.items()):
            if type(value) in (str, unicode, int):
                inputs.append(self.as_field(name, key, value))
            elif type(value) in (dict,):
                inputs.extend(self.to_fields("%s__%s" % (name, key), value))
            elif isinstance(value,list):
                inputs.append(self.as_list(name, key, value))
        return inputs

    # TODO: integer values don't need to be stored as string
    # TODO: floats not handled properly?
    def value_from_datadict(self, data, files, name):
        """A method that extends the widget to return values back to JSON

        Take values from POST or GET and convert back to JSON
        Takes all data variables that starts with fieldname__
        and converts fieldname__key__key = value into json[key][key] = value
        """
        json_obj = {}

        separator = "__"

        for key, value in data.items():
            if key.startswith(name+separator):
                dict_key = key[len(name+separator):].split(separator)

                prev_dict = json_obj
                for k in dict_key[:-1]:
                    if prev_dict.has_key(k):
                        prev_dict = prev_dict[k]
                    else:
                        prev_dict[k] = {}
                        prev_dict = prev_dict[k]

                prev_dict[dict_key[-1:][0]] = value
        try:
            prev_dict
        except NameError:
            pass
        else:
            return json.dumps(prev_dict)

    def render(self, name, value, attrs=None):
        """A method that extends the widget to render the JSON object

        Allow plain text version of JSON as well (for debugging)
        """
        # handle empty fields
        if value is None or value == '':
            value = '{}'

        json_obj = json.loads(value)
        inputs = self.to_fields(name, json_obj)

        # render JSON as plain text
        #inputs.append(value)

        return utils.safestring.mark_safe(u"".join(inputs))

class JSONEditableFormField(forms.Field):
    """A class representing an extension of forms.Field

    Uses JSONEditableWidget
    """
    widget = JSONEditableWidget

####
# todo: Text box type: as_text(); Add min/max to help or info by default or option?
####
class JSONConfigField(models.Field):
    """This is a custom field to be rendered on/returned from a form that is configured using a JSON object with the
    following format::

       {"type":0, "default":1.0, "min":0, "max":12, "help":"My Help Text", "info":"My info popover text", "label":"My Custom Field", "choices":["value 1", "value 2"]}

    the 5 attributes defined above should be self explanatory except type+choices, info:

    - 0 for char fields
    - 1 for text boxes  - not yet implemented
    - bool for checkboxes
    - choice for drop-down select boxes. (also requires "choices":["value 1", "value 2"]
    - info: creates an icon/popover in the label (like tooltips)

    .. note:: since the display order seemed to be basically random, I added alphabetic sorting:
              for key, value in sorted(json_obj.items())

    Example CSS styles::

        /* set popover width bigger than default */
        .popover {max-width: 800px;}

        /* color the info button to make it pop out */
        .info { color: rgb(26, 107, 181); }

    Example js to enable popovers::

       /* enable popovers - used on info button */
       $('.info').popover({placement: 'left', html: 'true'})
    """
    description = _("JSON")

    def db_type(self, connection):
        return 'text'

    def formfield(self, **kwargs):
        defaults = {'form_class': JSONConfigFormField}
        defaults.update(kwargs)
        return super(JSONConfigField, self).formfield(**defaults)

class JSONConfigWidget(forms.Widget):
    # TODO Add class docstring

    def get_help(self, value):
        """ Extract help text from value and return with span or nothing """
        if 'help' in value:
            help = u'<span class="help-block">%s</span>' % force_unicode(value['help'])
        else:
            help = ''
        return help

    def get_info(self, value):
        """ Extract info text from value and return with icon for pop-over or nothing """
        if 'info' not in value:
            info = ''
        else:
            info = u'<p class="pull-right info" data-toggle="popover" data-content="%s"> <i class="icon-info-sign"></i> </p>'\
                   % force_unicode(value['info'])
        return info

    def get_label(self, key, value):
        """ Return label text from value or build it from key """

        # todo: get label_suffix from form somehow
        label_suffix = ''
        if 'label' in value:
            label = force_unicode(value['label'])
        else:
            # capitalize just the first word
            #label = key.replace('_', ' ').capitalize()
            # capitalize all words
            label = key.split("_")
            label = " ".join(i.capitalize() for i in label)
        return label + label_suffix

    def get_tooltip(self, value):
        """ Extract info text from value and return with icon for pop-over or nothing """
        if 'tooltip' not in value:
            tooltip = ''
        else:
            tooltip = u'<p class="pull-right tooltip_link" data-toggle="tooltip" data-original-title="%s" href=""> <i class="icon-info-sign"></i> </p>'\
                   % force_unicode(value['tooltip'])
        return tooltip

    def get_validation(self, value):
        """ Extract validation info from value (or schema) and return for inclusion in input for jQuery Validation """
        validation = 'required="" '
        if 'min' in value and 'max' in value:
            validation = validation + 'range=' + force_unicode(value['min']) + ',' + force_unicode(value['max'])
        elif 'min' in value:
            validation = validation + 'min=' + force_unicode(value['min'])
        elif 'max' in value:
            validation = validation + 'max=' + force_unicode(value['max'])
        return validation

    def as_field(self, name, key, value):
        """ Render key, value as field """
        #Build the input attributes from the dictionary passed in as 'value'
        input_name = '%s_%s' % (name, key)
        attrs = self.build_attrs(name=input_name)
        if 'value' in value:
            attrs['value'] = force_unicode(value['value'])
        elif 'default' in value:
            attrs['value'] = force_unicode(value['default'])

        validation = self.get_validation(value)

        my_label = self.get_label(key, value)
        help_text = self.get_help(value)
        info = self.get_info(value)
        tooltip = self.get_tooltip(value)

        return u'<div class="row"><div class="span3point5"><label>%s%s%s</label></div><div class="span3">' \
               u'<input%s type="text" %s /> <span class="text-error" id="%s"></span>%s</div></div>' \
               % (info, tooltip, my_label, flatatt(attrs), validation, input_name + '_error', help_text)

    def as_checkbox(self, name, key, value):
        """ Render key, values as hidden/checkbox set

        - including hidden input to ensure 0 is posted if the box is not checked
        - to overwrite 1's previously chosen.

        ::

            <input type="hidden" name="the_checkbox" value="0" />
            <input type="checkbox" name="the_checkbox" value="1" />
         """
        #Build the input attributes from the dictionary passed in as 'value'
        input_name = '%s_%s' % (name, key)
        attrs = self.build_attrs(name=input_name)

        checked = ''
        if 'value' in value:
            #print "value['value']: ", value['value']
            if value['value'] == "1" or value['value'] == 1 or value['value'] == "on" or value['value'].upper() == "TRUE":
                checked = 'checked="checked"'
        elif 'default' in value:
            if value['default'] == 1 or value['default'] == "1" or value['default'] == "on" or str(value['default']).upper() == "TRUE":
                    checked = 'checked="checked"'

        my_label = self.get_label(key, value)
        help_text = self.get_help(value)
        info = self.get_info(value)
        tooltip = self.get_tooltip(value)
        #input_name = "MY ERROR"

        # if there isn't any help text for the checkbox, collapse it down to a single line.
        # still display the help text if it is present.
        if not help_text:
            div = u'<div class="row"><div class="span3" >' \
               u'' \
               u'<label style="display:inline;"> <input %s class="checkbox" type="hidden" value="0" %s /><input %s type="checkbox" value="1" %s style="margin-top:0px; margin-bottom:5px;"/>&nbsp;%s</label>%s%s</div></div>' \
               % (flatatt(attrs), checked, flatatt(attrs),  checked, my_label, info, tooltip)
        else:
            div =  u'<div class="row"><div class="span3" >' \
               u'' \
               u'<label style="display:inline;"> <input %s class="checkbox" type="hidden" value="0" %s /><input %s type="checkbox" value="1" %s style="margin-top:0px; margin-bottom:5px;"/>&nbsp;%s</label>%s%s</div></div>' \
               u'<div class="row"><div class="span3" style="padding-bottom:20px"><span class="text-error" id="%s"></span>%s&nbsp;</div></div>' \
               % (flatatt(attrs), checked, flatatt(attrs),  checked, my_label, info, tooltip, input_name + '_error',  help_text)

        return div


    def as_list(self, name, key, value):
        """ Render key, values as drop-down menu """
        #Build the input attributes from the dictionary passed in as 'value'
        input_name = '%s_%s' % (name, key)
        attrs = self.build_attrs(name=input_name)

        if 'value' in value:
            chosen = force_unicode(value['value'])
        elif 'default' in value:
            chosen = force_unicode(value['default'])
        else:
            chosen = ''

        my_options = '<option value="">Please select...</option>'
        for my_item in value['choices']:
            if my_item == chosen:
                selected = 'selected="selected" '
            else:
                selected = ''

            my_options = my_options + '<option '+selected+'value="'+my_item+'">'+my_item+'</option>'

        my_label = self.get_label(key, value)
        help_text = self.get_help(value)
        info = self.get_info(value)
        tooltip = self.get_tooltip(value)

        return u'<div class="row"><div class="span3"><label>%s%s%s</label></div>' \
               u'<div class="span3">' u'<select %s required>%s</select>%s</div></div>' \
               % (info, tooltip, my_label, flatatt(attrs), my_options, help_text)

    def as_choice_values_list(self, name, key, value):
        """ Render key, values as a list of checkboxes (each with a value box) """
        my_html = ''

        # value['values']
        counter = 1
        for my_item in value['choices']:
            # set default values for checked and input boxes
            checked = ''
            input_value = ""

            try:
                if my_item in value['default']:
                    checked = 'checked="checked"'
                    try:
                        input_value = value['values_defaults'][counter-1]
                    except:
                        input_value = "0"
            except:
                pass

            my_html += '</div><div class="row" style="margin:0px;">' \
                '<div class="span2" style="margin-left:8px;">' \
                    '<label style="display:inline;"><input type="checkbox" name="json_' + key + '_' + str(counter) +\
                       '" value="' + my_item + '" style="margin-top:-3px;" ' + checked + ' > ' \
                    + my_item + '</label>' \
                '</div>' \
                '<div class="span1">' \
                    '<input type="text" style="width: 150px; height:11px;" data-id="template_0" ' \
                    'name="json_' + value['values'] + '_' + str(counter) + '" value="' + str(input_value) + '"></input>' \
                '</div>' \
            '</div>'
            counter += 1

        my_label = self.get_label(key, value)
        help_text = self.get_help(value)
        info = self.get_info(value)
        tooltip = self.get_tooltip(value)

        return u'<div class="row" style="margin:0px;"><div class="span3point5" style="margin-left:0px;"><label>%s%s%s</label></div>' \
               u'<br/>&nbsp;<span class="pull-left">%s</span>%s</div><br/>' \
               % (info, tooltip, my_label, help_text, my_html)

    def as_hidden(self, name, key, value):
        """ Render key, value as hidden input """
        #Build the input attributes from the dictionary passed in as 'value'
        input_name = '%s_%s' % (name, key)
        attrs = self.build_attrs(name=input_name)
        if 'value' in value:
            attrs['value'] = force_unicode(value['value'])
        elif 'default' in value:
            attrs['value'] = force_unicode(value['default'])
        return u'<div style="display:none;"><input type="hidden" %s /></div>' \
               % (flatatt(attrs))


    def to_fields(self, name, json_obj):
        """Get list of rendered fields for json object"""
        inputs = []
        try:
            new_list = sorted(json_obj.items(), key=lambda k: k[1]['order'])
        except KeyError:
            new_list = sorted(json_obj.items())
        for key, value in new_list:
            if 'type' in value:
                if value['type'] == 0:
                    inputs.append(self.as_field(name, key, value))
                if value['type'] == 1:
                    inputs.append(self.as_field(name, key, value))
                if value['type'] == "text":
                    inputs.append(self.as_field(name, key, value))
                if value['type'] == "bool":
                    inputs.append(self.as_checkbox(name, key, value))
                if value['type'] == "choice":
                    inputs.append(self.as_list(name, key, value))
                if value['type'] == "choice_values":
                    inputs.append(self.as_choice_values_list(name, key, value))
                if value['type'] == "hidden":
                    inputs.append(self.as_hidden(name, key, value))
        inputs.append(u'<div style="display:none;"><input type="hidden" name="orig_json_obj" id="orig_json_obj" value="%s"></div>'
                      % escape(json.dumps(json_obj)))
        return inputs

    def value_from_datadict(self, data, files, name):
        try:
            json_obj = json.loads(data['orig_json_obj']) #.encode('unicode-escape'))
        except:
            #print "MISSING orig_json_object in value_from_datadict"
            #return None
            json_obj = json.loads(data['orig_json_obj'].encode('unicode-escape'))

        #print 'JSON Object is: ', json_obj
        separator = "_"
        for key, value in data.items():
            if key.startswith(name+separator):
                dict_key = key[len(name+separator):] #.split(separator)[0]
                if dict_key in json_obj:
                    key_values = json_obj[dict_key]
                    key_values['value'] = value
                    json_obj[dict_key] = key_values
        return json.dumps(json_obj)

    def render(self, name, value, attrs=None):
        if value is None or value == '':
            value = '{}'
        json_obj = json.loads(value)
        inputs = self.to_fields(name, json_obj)
        # render json as well
        #inputs.append(value)
        #return utils.safestring.mark_safe(u"<br />".join(inputs))
        return utils.safestring.mark_safe(u"".join(inputs)) + \
              '<script> $(document).ready(function () { $("form").validate({ rules: { } }); }); </script> '

class JSONConfigFormField(forms.Field):
    widget = JSONConfigWidget


class JSONConfigWidgetTwoColumn(JSONConfigWidget):
    """ Override widget to display JSONConfig object as TWO COLUMNS """
    def render(self, name, value, attrs=None):
        if value is None or value == '':
            value = '{}'
        json_obj = json.loads(value)
        inputs = self.to_fields(name, json_obj)

        hidden_inputs = []
        non_hidden = []
        for input in inputs:
            if 'type="hidden"' in input and 'class="checkbox"' not in input:
                hidden_inputs.append(input)
            else:
                non_hidden.append(input)

        # Open left div, half-way through fields close left div, open right div, at end close right div.
        #middle = ((len(inputs) - len(inputs)%2) / 2) + 1
        middle = ((len(non_hidden) - len(non_hidden)%2) / 2) + 1

        # find out how many checkboxes are in the first and second half, shift the middle accordingly
        checkbox_counter_1 = 0
        checkbox_counter_2 = 0
        loop_counter = 1
        for input in inputs:
            if 'class="checkbox"' in input:
                if loop_counter < middle:
                    checkbox_counter_1 += 1
                else:
                    checkbox_counter_2 += 1
        if abs(checkbox_counter_1 - checkbox_counter_2) > 0:
            middle = middle + ((checkbox_counter_1 - checkbox_counter_2)/3)  # or /2

        non_hidden.insert(0, '<div style="float: left; width: 49%;">')
        non_hidden.insert(middle, '</div><div style="float: right; width: 50%;">')
        #non_hidden.insert(-1, '</div>')
        non_hidden.extend(hidden_inputs)
        non_hidden.append('</div>')
        non_hidden.append('<script> $(document).ready(function () { $("form").validate({ rules: { } }); }); </script> ')

        # render json as well - good for debugging
        #non_hidden.append(value)

        #return utils.safestring.mark_safe(u"<br />".join(non_hidden))
        return utils.safestring.mark_safe(u"".join(non_hidden))
