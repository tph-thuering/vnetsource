from django.views.generic import TemplateView
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied

from data_services.models import DimUser
from ts_emod2.models import Scenario

import json


class DetailsView(TemplateView):
    template_name = 'ts_emod2/details/details.html'

    def get_context_data(self, **kwargs):
        context = super(DetailsView, self).get_context_data(**kwargs)
        context['nav_button'] = 'details'

        scenario_id = kwargs['scenario_id']

        dim_user = DimUser.objects.get(username=self.request.user.username)
        scenario = Scenario.objects.get(id=scenario_id)
        simulation = scenario.simulation

        # Check permissions
        if scenario.user != dim_user:
            raise PermissionDenied

        if scenario.extra_metadata:
            extra_metadata = scenario.extra_metadata

            if 'representative' in extra_metadata:
                scenario.is_representative = True
                if 'is_complete' in extra_metadata['representative']:
                    scenario.representative_is_complete = True
                else:
                    scenario.representative_is_completed = False
            else:
                scenario.is_representative = False

        input_files = self.get_input_files(scenario)
        output_files = self.get_output_files(scenario)

        context['scenario'] = scenario
        context['dim_user'] = dim_user
        context['simulation'] = simulation
        context['input_files'] = input_files
        context['output_files'] = output_files

        return context

    def get_input_files(self, scenario):
        input_files = []

        input_files.append({})
        input_files[-1]['json'] = json.dumps(json.loads(scenario.config_file.get_contents()),
                                                        indent=4, separators=(',', ': '))
        input_files[-1]['file_type'] = 'config'
        input_files[-1]['printed_name'] = 'Config.json'

        input_files.append({})
        input_files[-1]['json'] = json.dumps(json.loads(scenario.campaign_file.get_contents()),
                                                        indent=4, separators=(',', ': '))
        input_files[-1]['file_type'] = 'campaign'
        input_files[-1]['printed_name'] = 'Campaign.json (Interventions)'

        input_files.append({})
        input_files[-1]['json'] = json.dumps(json.loads(scenario.uncompiled_demographics_file.get_contents()),
                                                        indent=4, separators=(',', ': '))
        input_files[-1]['file_type'] = 'demographics'
        input_files[-1]['printed_name'] = 'Demographics.json'

        input_files.append({})
        # input_files[-1]['json'] = json.dumps(json.loads(get_rainfall_bin_file(dim_user, simulation)),
        #                                                 indent=4, separators=(',', ': '))
        input_files[-1]['file_type'] = 'rainfall-bin'
        input_files[-1]['printed_name'] = 'Rainfall.bin'
        input_files[-1]['short_file_type'] = 'rainfall'

        input_files.append({})
        input_files[-1]['json'] = json.dumps(json.loads(scenario.rainfall_json_file.get_contents()),
                                                        indent=4, separators=(',', ': '))
        input_files[-1]['file_type'] = 'rainfall-json'
        input_files[-1]['printed_name'] = 'Rainfall.bin.json'

        input_files.append({})
        # input_files[-1]['json'] = json.dumps(json.loads(get_humidity_bin_file(dim_user, simulation)),
        #                                                 indent=4, separators=(',', ': '))
        input_files[-1]['file_type'] = 'humidity-bin'
        input_files[-1]['printed_name'] = 'Humidity.bin'
        input_files[-1]['short_file_type'] = 'humidity'

        input_files.append({})
        input_files[-1]['json'] = json.dumps(json.loads(scenario.humidity_json_file.get_contents()),
                                                        indent=4, separators=(',', ': '))
        input_files[-1]['file_type'] = 'humidity-json'
        input_files[-1]['printed_name'] = 'Humidity.bin.json'

        input_files.append({})
        # input_files[-1]['json'] = json.dumps(json.loads(get_temperature_bin_file(dim_user, simulation)),
        #                                                 indent=4, separators=(',', ': '))
        input_files[-1]['file_type'] = 'temperature-bin'
        input_files[-1]['printed_name'] = 'Temperature.bin'
        input_files[-1]['short_file_type'] = 'temperature'

        input_files.append({})
        input_files[-1]['json'] = json.dumps(json.loads(scenario.temperature_json_file.get_contents()),
                                                        indent=4, separators=(',', ': '))
        input_files[-1]['file_type'] = 'temperature-json'
        input_files[-1]['printed_name'] = 'Temperature.bin.json'

        return input_files

    def get_output_files(self, scenario):
        try:
            output_files = []

            output_files.append({})
            output_files[-1]['json'] = json.dumps(json.loads(scenario.binned_report_json_file.get_contents()),
                                                             indent=4, separators=(',', ': '))
            output_files[-1]['file_type'] = 'binned-report-json'
            output_files[-1]['printed_name'] = 'BinnedReport.json'

            output_files.append({})
            output_files[-1]['json'] = json.dumps(json.loads(scenario.demographics_summary_json_file.get_contents()),
                                                             indent=4, separators=(',', ': '))
            output_files[-1]['file_type'] = 'demographics-summary-json'
            output_files[-1]['printed_name'] = 'DemographicsSummary.json'

            output_files.append({})
            output_files[-1]['json'] = json.dumps(json.loads(scenario.inset_chart_json_file.get_contents()),
                                                             indent=4, separators=(',', ': '))
            output_files[-1]['file_type'] = 'inset-chart-json'
            output_files[-1]['printed_name'] = 'InsetChart.json'

            output_files.append({})
            output_files[-1]['json'] = json.dumps(json.loads(scenario.vector_species_report_json_file.get_contents()),
                                                             indent=4, separators=(',', ': '))
            output_files[-1]['file_type'] = 'vector-species-report-json'
            output_files[-1]['printed_name'] = 'VectorSpeciesReport.json'
        except ObjectDoesNotExist:
            output_files = []

        return output_files