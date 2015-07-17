# -*- coding: utf-8 -*-
import json
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from vecnet.openmalaria.cts import continuousMeasuresDescription
from vecnet.openmalaria.output_parser import surveyFileMap
from data_services.models import Simulation, SimulationInputFile, SimulationOutputFile
from lib.templatetags.base_extras import set_notification
from ts_om_viz.utils import om_output_parser_from_simulation

class SimulationView(TemplateView):
    template_name = 'ts_om_viz/simulation.html'

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        sim_id = kwargs["id"]

        request = self.request
        if "survey_measure_id" in request.GET and "survey_third_dimension" in request.GET:
            context["survey_measure_id"] = int(request.GET["survey_measure_id"])
            context["survey_third_dimension"] = int(request.GET["survey_third_dimension"])
        context["sim_id"] = sim_id
        try:
            simulation = Simulation.objects.get(id=sim_id)

            # Get contents of xml input file and filename (if available)
            scenario_file = SimulationInputFile.objects.filter(simulations=simulation, name="scenario.xml")
            if "filename" in scenario_file[0].metadata:
                xml_filename = scenario_file[0].metadata["filename"]
            else:
                xml_filename = "scenario.xml"
            context["xml_filename"] = xml_filename
        except ObjectDoesNotExist:
            set_notification('alert-error',
                             '<strong>Error! Simulation %s does not exist </strong>' % sim_id,
                             self.request.session)
            return context
        except Exception as e:
            set_notification('alert-error',
                             '<strong>Error! %s </strong>' % e,
                             self.request.session)
            return context

        try:
            output_file = SimulationOutputFile.objects.get(simulation=simulation, name="output.txt")
            output_txt_filename = "output.txt"
        except:
            output_txt_filename = None

        try:
            output_file = SimulationOutputFile.objects.get(simulation=simulation, name="ctsout.txt")
            ctsout_txt_filename = "ctsout.txt"
        except:
            ctsout_txt_filename = None


        context["output_txt_filename"] = output_txt_filename
        context["ctsout_txt_filename"] = ctsout_txt_filename
        try:
            model_stdout_stderr_file = SimulationOutputFile.objects.get(simulation=simulation, name="model_stdout_stderr.txt")
            context["model_stdout"] = "model_stdout_stderr.txt"
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            pass

        try:
            output_parser = om_output_parser_from_simulation(simulation)
        except (TypeError, ValueError) as e:
            error_type = "%s" % type(e)
            error_type = error_type.replace("<", "").replace(">", "")
            set_notification('alert-error', "Error processing input or output files: (%s) %s" % (error_type, str(e)), self.request.session)
            return context
        try:
            survey_measures = {}
            for measure in output_parser.get_survey_measures():
                survey_measures[output_parser.get_survey_measure_name(measure_id=measure[0],
                                                        third_dimension=measure[1])] = measure
        except AttributeError:
            survey_measures = {}
        try:
            cts_measures = output_parser.get_cts_measures()
        except AttributeError:
            cts_measures = []

        context["survey_measures"] = survey_measures
        context["cts_measures"] = sorted(cts_measures)
        context["request"] = request
        return context

    def invalid_notification(self, err):
        set_notification('alert-error',
                         '<strong>Error! %s</strong>'% str(err.__str__()),
                         self.request.session)


def get_survey_data(request, sim_id, measure_id, bin_number):
    sim_id = int(sim_id)
    measure_id = int(measure_id)
    try:
        bin_number = int(bin_number)
    except ValueError:
        # Treat bin_number as species name
        pass
    simulation = get_object_or_404(Simulation, id=sim_id)
    output_parser = om_output_parser_from_simulation(simulation)
    try:
        data = output_parser.survey_output_data[(measure_id, bin_number,)]
    except KeyError:
        raise Http404("There is not measure (%s,%s) in simulation %s" % (measure_id, bin_number, sim_id))

    # Include measure_name and sim_id to http response for debug purpose
    result = {"measure_name": output_parser.get_survey_measure_name(measure_id=measure_id, third_dimension=bin_number),
              "sim_id": sim_id,
              "data": data,
              "description": surveyFileMap[measure_id][2]
    }
    return HttpResponse(json.dumps(result), content_type="application/json")


def get_cts_data(request, sim_id, measure_name):
    sim_id = int(sim_id)
    simulation = get_object_or_404(Simulation, id=int(sim_id))
    output_parser = om_output_parser_from_simulation(simulation)
    try:
        data = output_parser.cts_output_data[measure_name]
    except KeyError:
        raise Http404("There is not measure %s in simulation %s" % (measure_name, sim_id))
    result = {
        "measure_name": measure_name,
        "sim_id": sim_id,
        "data": data,
        "description": continuousMeasuresDescription.get(measure_name, "")
    }
    return HttpResponse(json.dumps(result), content_type="application/json")