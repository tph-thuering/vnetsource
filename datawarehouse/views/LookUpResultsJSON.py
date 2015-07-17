########################################################################################################################
# VECNet CI - Prototype
# Date: 3/9/2015
# Institution: University of Notre Dame
# Primary Authors:
#    Anna Alber <aalber1@nd.edu>
########################################################################################################################
from django.db.models import get_app, get_models
from django.db.models import get_app, get_models
import inspect
from  datawarehouse.models import LutInterventionIrsCoveragesAdmin1, LutInterventionItnCoveragesAdmin1,LutSpecies,LutEntomologicalEndpoint
from datawarehouse.views.LookUpResults import LookUpResults


import operator
from django.db.models import Q
import  json

from django.http import HttpResponse
from django.shortcuts import  render_to_response
from django.views.generic import ListView
from collections import OrderedDict
from django.db.models import get_app, get_models
from datawarehouse.models import LutSpecies
import inspect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt



TABLE_DICTIONARY = {'LutSpecies':'lut_species', 'LutEntomologicalEndpoint':'lut_entomological_endpoint',
                    'LutInterventionIrsCoveragesAdmin1':'lut_intervention_irs_coverage_admin1',
                    'LutInterventionItnCoveragesAdmin1':'lut_intervention_irs_coverage_admin1' }
TABLE_OBJ_DICTIONARY = {'LutInterventionIrsCoveragesAdmin1':LutInterventionIrsCoveragesAdmin1,
                        'LutInterventionItnCoveragesAdmin1':LutInterventionItnCoveragesAdmin1,
                        'LutSpecies':LutSpecies,
                        'LutEntomologicalEndpoint':LutEntomologicalEndpoint}
class LookUpResultsJSON:
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(LookUpResultsJSON, self).dispatch(request, *args, **kwargs)

    def __init__(self):
      self.results = {}

    def fill_in_metadata(self):
        app = get_app('datawarehouse')
        for model in get_models(app):                       # loop over datawarehouse tables
            for f in inspect.getmembers(model):
                if f[0] == 'lookup' and f[1] == True:
                    self.results[model._meta.object_name] = [f.name for f in model._meta._fields()]
        return self.results

    def get_results_page(self,results, page_number, rows_number):

        offset_number = int((int(page_number)-1))*int(rows_number)
        beg = int(offset_number)
        end = int(rows_number) + beg
        print '\n\n\n get beginning and end of the page ', beg, '->', end
        results_page = results[beg:end]
        return results_page

    def get_rows(self,showFields,results, page_number, rows_number):

        r_list = []
        results_page = self.get_results_page(results, page_number, rows_number)
        print '\n rows number, page_number ', rows_number, page_number

        n = 0
        for r in results_page:
            n = n+1
            r_dict = {}

            for f in showFields :
                #print '\n field f is ', f
                if str(f) != 'id': #todo:add more fields here
                    r_dict[f] = r.get_field(f)

            r_list.append(r_dict)
        print '\n list is ', r_list
        return r_list

    def get_range(self, string, separator):
        return [x.strip() for x in string.split(separator)]


    def get_all_filters(self,filtering,queryset, sorting_order):
        kwargs = {}
        result = queryset
        try:
            filters = json.loads(filtering)

            print '\n filters are now ', filters
            for filter in filters:
                print '\n for filter in filters ', filter

                argument_list = []
                if str(filter["op"]) == 'similar':
                    value_list = self.get_range(str(filter["value"]), ",")
                    for l in value_list:
                        argument_list.append(Q(**{str(filter['field']) + '__icontains': l}))

                elif str(filter["op"]) == 'equal':
                    # kwargs[str(filter['field'])] = str(filter["value"])
                    value_list = self.get_range(str(filter["value"]), ",")
                    for l in value_list:
                        print '\n in l is (', l, ')'
                        argument_list.append(Q(**{str(filter['field']) + '__iexact': l}))

                elif str(filter["op"]) == 'notequal':
                    argument_list.append(~Q(**{str(filter['field']) + '__iexact': filter["value"]}))

                elif str(filter["op"]) == 'between':
                    range = self.get_range(str(filter["value"]), ":")
                    kwargs = {"%s__range" % (str(filter['field'])): (str(range[0]), str(range[1]))}

                elif str(filter["op"]) == 'less':
                    kwargs = {"%s__lt" % (str(filter['field'])):  (filter["value"])}
                elif str(filter["op"]) == 'greater':
                    kwargs = {"%s__gt" % (str(filter['field'])):  (filter["value"])}
                elif str(filter["op"]) == 'nofilter':
                    try:
                         del kwargs[str(filter['field'])]
                    except:
                        try:
                            del argument_list[str(filter['field'])]
                        except:
                            print '\n was not able to remove filter'

                result = result.filter(**kwargs).order_by(sorting_order)
                print '\n before argument_list ', argument_list
                result = result.filter(reduce(operator.or_, argument_list))

        except:
            pass
        return result

    #check what sorting_order does

    def get_sorting_order(self,request,sorting_order):
        ordering = 'asc'

        try:
            sorting_order = request.REQUEST['sort']
            ordering = request.REQUEST['order']
            print '\n try sorting_order is ', sorting_order
            print '\n try ordering is ', ordering

        except:
            pass

        if ordering == 'desc':
            sorting_order = '-'+str(sorting_order)
        print '\n sorting_order is ', sorting_order
        return sorting_order

    ###########################


    ###
    #views.py
    ####


    def get_results(self,queryset, sorting_order, request):
        """ Gets data based on the search type and passed parameters

        @param queryset: result query set
        @param sorting_order: string
        @param request: http request
        @return: results

        """

        results = {}
        page_number = 1
        ordering = 'asc'
        rows_number = 10
        offset_number = (page_number-1)*rows_number
        #sorting
        sorting_order = self.get_sorting_order(request,sorting_order)
        print '\n finished sorting ', sorting_order

        #filter
        try:
             results['results'] = queryset
        #     results['results'] = self.get_all_filters(request.REQUEST['filterRules'],queryset, sorting_order)
        #     print '\n got all_filters ', results['results']
        except:
        #     results['results'] = queryset
             print '\n did not get queryset '
        #paging
        try:
            page_number = request.REQUEST['page']
            ordering = request.REQUEST['order']
            rows_number = request.REQUEST['rows']
            offset_number = (page_number-1)*rows_number
        except:
            pass
        results['results'] = results['results'].order_by(sorting_order)
        results['ordering'] = ordering
        results['rows_number'] = rows_number
        results['page_number'] = page_number
        results['sorting_order'] = sorting_order
        results['offset_number'] = offset_number
        results['total'] = results['results'].count()
        print '\n what is total? ', results['total']
        return results

    def process_table_data_for_json(self,request, table_obj, showFields):
        print "\n IN PROCESS DATA FOR JSON 2"
        dict_page = {}
        queryset = table_obj.objects.all()
        results = self.get_results(queryset, 'id',request)
        dict_page['theFields'] = showFields
        title_dict = {'LutEntomologicalEndpoint':'Entomological Parameters', 'LutInterventionIrsCoveragesAdmin1':'IRS Coverage in Africa',
                      'LutInterventionItnCoveragesAdmin1':'Intervention ITN Coverage in Africa', 'LutSpecies':'Species Bionomics'}

        url = '/datawarehouse/alltables?isajax=true&tablename='+table_obj.__name__#get_url( str(tablename.__name__))

        if 'isajax' in request.REQUEST:
            print '\n in ajax in process_table_data_for_json', table_obj.__name__, ' and total is ', results['total']
            dict_page['total'] = results['total']
            dict_page['rows'] = self.get_rows(showFields, results['results'], int(results['page_number']), int(results['rows_number']))
            result_json = json.dumps(dict_page)
            return HttpResponse(result_json)
        return render_to_response('datawarehouse/luresults_all.html', {'showFields':showFields, 'url':url, 'title':title_dict[table_obj.__name__]})
    #below are test specific functions
    def test(self,request):

        """
            The results view takes a list of url arguments, queries the database
            and returns the search results as a Django results object for the
            tabluar view.
        """

        # queryset = Mali_Collection.objects.all()
        # sorting_order = 'asc'
        print '\n\n\n\n\n =====   in test'
        showFields = []
        try:
            tablename = request.REQUEST['tablename']
            table_obj  = TABLE_OBJ_DICTIONARY [tablename]
            #tablename = TABLE_DICTIONARY[table]
        except:
            try:
                tablename = tablename.__name__
                table_obj  = TABLE_OBJ_DICTIONARY [tablename]
                print '\n\n\n\n did not find a table name'

            except:
                table_obj = LutInterventionIrsCoveragesAdmin1

        for field in table_obj._meta.fields:
            if str(field.name) != 'id':
                showFields.append(field.name)

        return self.process_table_data_for_json(request,table_obj, showFields)



    def process_table_data(self,request):
        """ Performs back end filtering for retreived results
        @param request: http request
        @return: results
        @rtype: query set

        """

        json_var = {
                "arabiensis": {
                    "Acquire Modifier": 0.3,
                    "Adult Life Expectancy": 7.5,
                    "Anthropophily": 0.5,
                    "Aquatic Arrhenius_1": "842e+8",#84200000000,
                    "Aquatic Arrhenius_2": 8250,
                    "Aquatic Mortality Rate": 0.1,
                    "Days Between Feeds": 2,
                    "Egg Batch Size": 120,
                    "Habitat Type":"TEMPORARY RAINFALL:225+e7",#2250000000.0",
                    "Immature Duration": 2,
                    "Indoor Feeding Fraction": 0.4,
                    "Infected Arrhenius_1": "117+e9",#117000000000,
                    "Infected Arrhenius_2": 8336,
                    "Infected Egg Batch Factor": 0.8,
                    "Infectious Human Feed Mortality Factor": 1.1,
                  #  "Required_Habitat_Factor":2250000000.0,
                    "Transmission Rate": 0.8
                },
                "funestus": {
                    "Acquire Modifier": 0.3,
                    "Adult Life Expectancy": 8.5,
                    "Anthropophily": 0.97,
                    "Aquatic Arrhenius_1": "842e+8",#84200000000,
                    "Aquatic Arrhenius_2": 8250,
                    "Aquatic Mortality Rate": 0.1,
                    "Days Between Feeds": 2,
                    "Egg Batch Size": 120,
                    "Habitat Type": "WATER VEGETATION:75+e7",#750000000.0",
                    "Immature Duration": 2,
                    "Indoor Feeding Fraction": 0.75,
                    "Infected Arrhenius_1": "117+e9",#117000000000,
                    "Infected Arrhenius_2": 8336,
                    "Infected Egg Batch Factor": 0.8,
                    "Infectious Human Feed Mortality Factor": 1.1,
                   # "Required_Habitat_Factor": 750000000.0,
                    "Transmission Rate": 0.8
                },
                "gambiae": {
                    "Acquire Modifier": 0.3,
                    "Adult Life Expectancy": 8.5,
                    "Anthropophily": 0.97,
                    "Aquatic Arrhenius_1": "842e+8",#84200000000,
                    "Aquatic Arrhenius_2": 8250,
                    "Aquatic Mortality Rate": 0.1,
                    "Days Between Feeds": 2,
                    "Egg Batch Size": 120,
                    "Habitat Type":"TEMPORARY RAINFALL:55+e7",#5500000000.0",
                    "Immature Duration": 2,
                    "Indoor Feeding Fraction": 0.7,
                    "Infected Arrhenius_1": "117+e9",#117000000000,
                    "Infected Arrhenius_2": 8336,
                    "Infected Egg Batch Factor": 0.8,
                    "Infectious Human Feed Mortality Factor": 1.1,
                   # "Required_Habitat_Factor": 5500000000.0,
                    "Transmission Rate": 0.8
                },
                "minor": {
                    "Acquire Modifier": 0.3,
                    "Adult Life Expectancy": 7,
                    "Anthropophily": 0.2,
                    "Aquatic Arrhenius_1": "842e+8",#84200000000,
                    "Aquatic Arrhenius_2": 8250,
                    "Aquatic Mortality Rate": 0.1,
                    "Days Between Feeds": 2,
                    "Egg Batch Size": 120,
                    "Habitat Type": "CONSTANT:375+e5, TEMPORARY RAINFALL:375+e5, WATER VEGETATION:375+e5",
                    "Immature Duration": 2,
                    "Indoor Feeding Fraction": 0.1,
                    "Infected Arrhenius_1": "117+e9",#117000000000,
                    "Infected Arrhenius_2": 8336,
                    "Infected Egg Batch Factor": 0.8,
                    "Infectious Human Feed Mortality Factor": 1.1,
                   # "Required_Habitat_Factor":  37500000.0,
                    "Transmission Rate": 0.8
                }
            }

        #todo:change to keys iterator
        for key in  list(json_var.keys()):
             json_var[key]["Species"]= "An."+ key

        #showFields is not used, but left here for reference
        #showFields = sorted(json_var["minor"].keys(), reverse=True)

        json_var_result_1 = {}
        json_var_result_1["rows"] = []
        json_var_result_2 = {}
        json_var_result_2["rows"] = []

        fields_1 = ["Species","Acquire Modifier",
                    "Adult Life Expectancy",
                    "Anthropophily",
                    "Transmission Rate",
                    "Habitat Type"
                    ]
        fields_2 = ["Species",
                    "Immature Duration",
                    "Indoor Feeding Fraction",
                    "Infected Arrhenius_1",
                    "Infected Arrhenius_2",
                    "Infected Egg Batch Factor",
                    "Infectious Human Feed Mortality Factor",
                    "Aquatic Arrhenius_1",
                    "Aquatic Arrhenius_2",
                    "Aquatic Mortality Rate",
                    "Days Between Feeds",
                    "Egg Batch Size"
                    ]

        json_var_result_1["theFields"] = fields_1
        json_var_result_2["theFields"] = fields_2

        tablename = "lut_vectorspecies_param"
        url_1 = '/datawarehouse/lookuptable/?isajax=true&isone=true&tablename='+tablename#get_url( str(tablename.__name__))
        url_2 = '/datawarehouse/lookuptable/?isajax=true&istwo=true&tablename='+tablename#get_url( str(tablename.__name__))
        results = self.fill_in_metadata()

        if 'isajax' in request.REQUEST and 'isone' in request.REQUEST:
            json_var_result_1["total"] = 4
            for key, value in json_var_result_1["rows"]:
                if key not in fields_1:
                    del json_var_result_1[key]

            for key in  list(json_var.keys()):
                json_var_result_1["rows"].append(json_var[key])

            result_json_1 = json.dumps(json_var_result_1)
            return HttpResponse(result_json_1)

        elif 'isajax' in request.REQUEST and 'istwo' in request.REQUEST:
            json_var_result_2["total"] = 4
            for key, value in json_var_result_2["rows"]:
                if key not in fields_2:
                    del json_var_result_2[key]

            for key in  list(json_var.keys()):
                json_var_result_2["rows"].append(json_var[key])

            result_json_2 = json.dumps(json_var_result_2)
            return HttpResponse(result_json_2)

        else:
            print '\n IN ELSE ', request.REQUEST

        return render_to_response('datawarehouse/luresults_json.html', { 'results':results, 'fields_1': fields_1, 'url_1':url_1,'fields_2': fields_2, 'url_2':url_2})


    def process_table_data_simple(self,request):
        """ Performs back end filtering for retreived results
        @param request: http request
        @return: results
        @rtype: query set

        """
        json_var = {
                "arabiensis": {

                    "Anthropophily": 0.5,
                    "Adult Life Expectancy": "M=8",
                    "Larval Habitat": "Temporary Rainfall",
                    "Average Daily Biting Rate": "H=40,M=20,L=2",
                    "Indoor Feeding Fraction": 0.5

                },
                "funestus": {
                     "Anthropophily": 0.9,
                    "Adult Life Expectancy": "H=10",
                    "Larval Habitat": "Water Vegetation",
                    "Average Daily Biting Rate": "H=40,M=20,L=2",
                    "Indoor Feeding Fraction": 0.8

                },
                "gambiae": {
                    "Anthropophily": 0.9,
                    "Adult Life Expectancy": "H=10",
                    "Larval Habitat": "Temporary Rainfall",
                    "Average Daily Biting Rate": "H=40,M=20,L=2",
                    "Indoor Feeding Fraction": 0.8

                },
                 "pharaonis": {
                     "Anthropophily": 0.5,
                    "Adult Life Expectancy": "L=6",
                    "Larval Habitat": "Constant," + '\n'+"Temporary Rainfall"+'\n' + "Water Vegetation",

                    "Average Daily Biting Rate": "H=40,M=20,L=2",
                    "Indoor Feeding Fraction": 0.5

                },

                "merus": {
                     "Anthropophily": 0.5,
                    "Adult Life Expectancy": "L=6",
                    "Larval Habitat": "Temporary Rainfall",
                    "Average Daily Biting Rate": "H=40,M=20,L=2",
                    "Indoor Feeding Fraction": 0.5

                },
                 "melas": {
                     "Anthropophily": 0.5,
                    "Adult Life Expectancy": "L=6",
                    "Larval Habitat": "Temporary Rainfall, Water Vegetation",
                    "Average Daily Biting Rate": "H=40,M=20,L=2",
                    "Indoor Feeding Fraction": 0.5

                },
                "minor": {
                     "Anthropophily": 0.5,
                    "Adult Life Expectancy": "L=6",
                    "Larval Habitat": "Constant, Temporary Rainfall, Water Vegetation",
                    "Average Daily Biting Rate":"H=40,M=20,L=2",
                    "Indoor Feeding Fraction": 0.4

                },
                "moucheti": {
                     "Anthropophily": 0.5,
                    "Adult Life Expectancy": "L=6",
                    "Larval Habitat": "Constant, Temporary Rainfall, Water Vegetation",
                    "Average Daily Biting Rate": "H=40,M=20,L=2",
                    "Indoor Feeding Fraction": 0.2

                },
                 "nili": {
                     "Anthropophily": 0.1,
                    "Adult Life Expectancy": "L=6",
                    "Larval Habitat": "Constant, Temporary Rainfall, Water Vegetation",
                    "Average Daily Biting Rate": "H=40,M=20,L=2",
                    "Indoor Feeding Fraction": 0.2

                },

                "coustani alpha": {
                     "Anthropophily": 0.1,
                    "Adult Life Expectancy": "L=6",
                    "Larval Habitat": "Constant,Temporary Rainfall, Water Vegetation ",
                    "Average Daily Biting Rate":"H=40,M=20,L=2",
                    "Indoor Feeding Fraction": 0.2

                },
                 "coustani betta": {
                     "Anthropophily": 0.1,
                    "Adult Life Expectancy": "L=6",
                    "Larval Habitat": "Constant, Temporary Rainfall, Water Vegetation",
                    "Average Daily Biting Rate": "H=40,M=20,L=2",
                    "Indoor Feeding Fraction": 0.2

                }
            }

        for key in  list(json_var.keys()):
             json_var[key]["Species"]= "An."+ key
        showFields = sorted(json_var["minor"].keys(), reverse=True)

        json_var_result = {}
        json_var_result["rows"] = []

        json_var_result["theFields"] = showFields
        result_json = json.dumps(json_var_result)

        tablename = "lut_vectorspecies_param"
        url = '/datawarehouse/simpleparam/?isajax=true&tablename='+tablename#get_url( str(tablename.__name__))

        results = self.fill_in_metadata()

        if 'isajax' in request.REQUEST:
            json_var_result["total"] = 11

            for key in  list(json_var.keys()):
             json_var_result["rows"].append(json_var[key])

            result_json = json.dumps(json_var_result)
            return HttpResponse(result_json)

        else:
            print '\n IN ELSE ', request.REQUEST

        return render_to_response('datawarehouse/vector_species.html', { 'results':results, 'fields': showFields, 'url':url})


    def get_url(tablename):
        print '\n tablename is in url ', tablename

        url = "/datawarehouse/lookuptable/?isajax=true&tablename="+tablename #todo: check isajax

        return url

class LookUpResults(ListView, LookUpResultsJSON):
    """This view is used to render the lookup tables. It checks all
    models in the datawarehouse app for a field called lookup. If
    that field is found, then the model is queried and added to the
    results.
    """
    results = {}
    template_name = 'datawarehouse/luresults.html'                      # template to render to

    def get_context_data(self, **kwargs):
        """This method generates context data that is returned to the template.
        """
        context = super(LookUpResults, self).get_context_data(**kwargs) # call the super
        self.__init__()
        context['results'] = self.results                               # add results to the context
        return context

    def get_queryset(self):
        """This method is responsible for getting the querysets and appending them
        to the results list.
        """
        self.fill_in_metadata()
        # app = get_app('datawarehouse')
        # for model in get_models(app):                       # loop over datawarehouse tables
        #     for f in inspect.getmembers(model):
        #         if f[0] == 'lookup' and f[1] == True:
        #             self.results[model._meta.object_name] = [f.name for f in model._meta._fields()]

    def get_ordered_list(self, elements):
        """This method creates a list of ordered dictionaries using elements.
        """
        ordered = list()
        for obj in elements:
            od = OrderedDict((field.name, field.value_to_string(obj)) for field in obj._meta.fields)
            ordered.append(od)
        return ordered
