from django.db import models
from ts_emod2.models import ScenarioTemplate


class LocationPickerTemplate(models.Model):
    scenario_template = models.ForeignKey(ScenarioTemplate)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return str(self.scenario_template)

    class Meta:
        db_table = 'ts_emod_basic_location_picker_template'
        verbose_name = "LocationPickerTemplate"
        verbose_name_plural = "LocationPickerTemplates"