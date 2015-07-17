########################################################################################################################
# VECNet CI - Prototype
# Date: 4/5/2013
# Institution: University of Notre Dame
# Primary Authors:
#   Robert Jones <Robert.Jones.428@nd.edu>
########################################################################################################################

# Imports that are external to the ts_emod app

from django.db import models
from django.contrib.auth.models import User

import ast
import json

# Imports that are internal to the ts_emod app

from ts_emod.fields import JSONEditableField, JSONConfigField


class ConfigData(models.Model):
    """ConfigData Table

    Model that describes the ConfigData table
    For storing data used by the framework to build/augment/configure the app.
    """
    # TODO Add attribute docstring(s)
    class Meta:
        app_label = 'ts_emod'
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=100, blank=True)
    misc = models.CharField(max_length=256, null=True, blank=True)
    json = JSONConfigField()
    #json = models.CharField(max_length=8560)

    def __unicode__(self):
        """ A method that extends the model to return the name of the object on call """
        return self.name


class Intervention(models.Model):
    """Intervention Table

    Model that describes the Intervention table
    Intervention records are created by users for use in scenarios
    """
    # TODO Add attribute docstring(s)
    # TODO Add method docstring(s)
    class Meta:
        app_label = 'ts_emod'
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    json = JSONEditableField()
    configdata = models.ForeignKey(ConfigData, null=True, related_name='Intervention_configdata')
    orig_json_obj = models.CharField(max_length=7048, null=True, blank=True)
    settings = models.CharField(max_length=2048, null=True, blank=True)
    created_by = models.ForeignKey(User, null=True, related_name='tsIntervention_created_by')
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)
    # Flag indicating whether or not this scenario is available to users other than the creator
    is_public = models.BooleanField(default=False)

    def json_as_table(self):
        return_string = ""

        if self.json is not None:
            try:
                temp_dict = json.loads(self.json)
            except ValueError:
                temp_dict = ast.literal_eval(self.json)

            # pull name and class to the top of the details
            #if 'my_name' in temp_dict:
            #    return_string += "<tr><td>Name</td><td>"
            #    return_string += str(temp_dict['my_name']) + "</td></tr>"
            if 'class' in temp_dict:
                return_string += "<tr><td>Type</td><td>"
                return_string += str(temp_dict['class']) + "</td></tr>"

            for key, value in temp_dict.items():
                if key in ('my_name', 'class'):
                    continue  # don't display these again, handled above
                return_string += "<tr><td>" + key.replace("_", " ").title() + "</td><td>"
                return_string += str(value) + "</td></tr>"

        return return_string

    def get_class(self):
        return_string = ""

        if self.json is not None:
            try:
                temp_dict = json.loads(self.json)
            except ValueError:
                temp_dict = ast.literal_eval(self.json)

            for key, value in temp_dict.items():
                if key == 'class':
                    return_string = value
                    next

        return return_string

    def __unicode__(self):
        """ A method that extends the model to return the name of the object on call """
        return self.name


class Sweep(models.Model):
    """Sweep Table

    Model that describes the Sweep table
    Records are created by users to represent scenario sweeps.
    """

    class Meta:
        app_label = 'ts_emod'
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    misc = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(User, null=True, related_name='tsSweep_created_by')
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)
    #: Flag indicating whether or not this scenario is available to users other than the creator
    is_public = models.BooleanField(default=False)

    def __unicode__(self):
        """ A method that extends the model to return the name of the object on call """
        return self.name


class Species(models.Model):
    """Species Table

    Model that describes the Species table
    Species records are created by users for use in scenarios
    """
    # TODO Add attribute docstring(s)
    # TODO Add method docstring(s)

    class Meta:
        app_label = 'ts_emod'
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    json = JSONEditableField()
    configdata = models.ForeignKey(ConfigData, null=True, related_name='Species_configdata')
    orig_json_obj = models.CharField(max_length=7048, null=True, blank=True)
    #settings = models.CharField(max_length=7048, null=True, blank=True)
    created_by = models.ForeignKey(User, null=True, related_name='tsSpecies_created_by')
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)
    #: Flag indicating whether this scenario is a template or actual species instance
    is_template = models.BooleanField(default=False)
    #: Flag indicating whether or not this scenario is available to users other than the creator
    is_public = models.BooleanField(default=False)
    #: Many-to-many relationship, but won't have Scenario ID in middle of wizard (unless editing existing scenario)
    #:
    #: - save list of species created, connect to Species in done method
    #scenarios = models.ManyToManyField(Scenario) #models.TextField(null=True, blank=True)
    ## A method that extends the model to return the name of the object on call
    #

    def settings_as_table(self):
        temp_species_settings = self.settings.replace("config.json/parameters/", "").replace("'", "")
        temp_species_settings = temp_species_settings.replace("[", "").replace("]", "")

        return_string = ""
        for a_setting in temp_species_settings.split(", "):
            key_value = a_setting.split("=")
            return_string += "<tr><td>" + key_value[0].replace("_", " ") + "</td><td>" + \
                             key_value[1].replace("_", " ").title() + "</td></tr>"

        return return_string

    def json_as_table(self):
        return_string = ""

        if self.json is not None:
            try:
                temp_dict = json.loads(self.json)
            except ValueError:
                temp_dict = ast.literal_eval(self.json)

            for key, value in temp_dict[self.name].items():
                return_string += "<tr><td>" + key.replace("_", " ") + "</td><td>"
                if key == "Habitat_Type" or key == "Required_Habitat_Factor":
                    for habitat_selection in value:
                        return_string += str(habitat_selection).replace("_", " ") + "<br/>"
                else:
                    return_string += str(value)

                return_string += "</td></tr>"

        return return_string

    def __unicode__(self):
        return self.name