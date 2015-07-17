from tastypie.resources import ModelResource
from tastypie.api import Api
from tastypie import fields
from data_services.models import *
from datawarehouse.models import LutMapSiteid, LutSpecies, LutEntomologicalEndpoint, DimSource, \
    LutInterventionItnCoveragesAdmin1, LutInterventionIrsCoveragesAdmin1


class LocationResource(ModelResource):
    """Tastypie resource for the Location table."""


    class Meta:
        queryset = DimLocation.objects.all()
        resource_name = 'DimLocation'
        fields = ['admin007', 'admin0', 'admin1', 'admin2']
        allowed_methods = ['get']
        include_resource_uri = False


class SourceResource(ModelResource):
    """Tastypie resource for the Source table."""


    class Meta:
        queryset = DimSource.objects.all()
        resource_name = 'DimSource'
        fields = ['source', 'file_uid']
        allowed_methods = ['get']
        include_resource_uri = False


class LutInterventionItnCoveragesAdmin1Resource(ModelResource):
    """Tastypie resource for the LutInterventionItnCoveragesAdmin1 table."""

    class Meta:
        queryset = LutInterventionItnCoveragesAdmin1.objects.all()
        resource_name = 'LutInterventionItnCoveragesAdmin1'
        fields = ["id", "country", "province_name", "percent_of_children_under_5_years_sleeping_under_a_bednet",
                  "the_estimated_percent_households_with_itn",
                  "percent_itn_all", "year", "source", "source_url"]
        #fields = ['source', 'file_uid']
        allowed_methods = ['get']
        include_resource_uri = False
        limit = 0

    def dehydrate(self, bundle):
        bundle.data['field_order'] = ("id,country,province_name,the_estimated_percent_households_with_itn,"
                    "percent_of_children_under_5_years_sleeping_under_a_bednet,percent_itn_all,source,source_url,year")
                                      #, "province_name", "itn_5s", "households_with_itn",
                                      #"itn_all", "itn_year", "itn_source", "itn_source_url")
        return bundle

class LutInterventionIrsCoveragesAdmin1Resource(ModelResource):
    """Tastypie resource for the LutInterventionItnCoveragesAdmin1 table."""

    class Meta:
        queryset = LutInterventionIrsCoveragesAdmin1.objects.all()
        resource_name = 'LutInterventionIrsCoveragesAdmin1'
        fields = ["id", "country", "province_name", "percent_of_the_population_protected_by_irs",
                  "year", "source", "source_url"]
        #fields = ['source', 'file_uid']
        allowed_methods = ['get']
        include_resource_uri = False
        limit = 0

    def dehydrate(self, bundle):
        bundle.data['field_order'] = ("id,country,province_name,percent_of_the_population_protected_by_irs,"
                    "source,source_url,year")
        return bundle


class EntEndResource(ModelResource):
    """Tastypie resource for the Entomological Endpoint table."""
    source = fields.ForeignKey(SourceResource, 'source', full=True, null=True)
    file_uid = fields.ForeignKey(SourceResource, 'file_uid', full=True, null=True)

    class Meta:
        queryset = LutEntomologicalEndpoint.objects.all()
        resource_name = 'LutEntomologicalEndpoint'
        allowed_methods = ['get']
        include_resource_uri = False

    def dehydrate(self, bundle):
        bundle.data['field_order'] = ("id,impact_human_landing_rates,impact_direct_mortality,"
                                      "impact_vector_mosquito_abundance_in_treated_area,movement_away_from_a_point_source,"
                                      "impact_rate_of_entry_into_treated_area,impact_exit_rate_from_treated_area,"
                                      "impact_percent_of_blood_fed,impact_number_or_percent_of_blood_fed,"
                                      "impact_sporozoite_rate,impact_number_of_gravid_and_parous_females,"
                                      "impact_rate_of_inhibition_of_adult_emergence,impact_larval_and_pupal_density,"
                                      "impact_lethality_to_f1_females,possess_the_desired_trait,establishment_within_a_cage_population,"
                                      "mating_competitiveness,duration_of_effective_life_or_replacement_time,"
                                      "number_of_new_infections_among_human_cohort,source,file_uid")

        return bundle


class SpeciesResource(ModelResource):
    """Tastypie resource for the Species table."""
    location_key = fields.ForeignKey(LocationResource, 'location_key', full=True)


    class Meta:
        queryset = LutSpecies.objects.all()
        resource_name = 'LutSpecies'
        allowed_methods = ['get']
        include_resource_uri = False

    def dehydrate(self, bundle):
        # bundle.data['field_order'] = ("species,form,form_of_larval_habitat,flight_range,daily_adult_survival_rate,"
        #                               "location_key_resource_uri,admin007,admin0,admin1,admin2,source_key,"
        #                               "vector_status,larval_survival_rate,indoor_feeding_rate,human_blood_index,"
        #                               "peak_biting_time,length_of_feeding_cycle,LutSpecies_resource_uri,"
        #                               "pre_feeding_resting_habits,post_feeding_resting_habits,sugar_meal_frequency,"
        #                               "sugar_sources,id")
        bundle.data['field_order'] = ("id,species,form,form_of_larval_habitat,flight_range,daily_adult_survival_rate,"
                                      "admin007,admin0,admin1,admin2,source_key,"
                                      "vector_status,larval_survival_rate,indoor_feeding_rate,human_blood_index,"
                                      "peak_biting_time,length_of_feeding_cycle,"
                                      "pre_feeding_resting_habits,post_feeding_resting_habits,sugar_meal_frequency,"
                                      "sugar_sources")
        return bundle


class MapSiteIDResource(ModelResource):
    """Tastypie resource for the Malaria Atlas project Site ID table."""
    class Meta:
        queryset = LutMapSiteid.objects.all()
        resource_name = 'LutMapSiteid'
        allowed_methods = ['get']
        fields = ['geom']
        
Lookup = Api(api_name='Lookup')
Lookup.register(LocationResource())
Lookup.register(SpeciesResource())
Lookup.register(EntEndResource())
Lookup.register(MapSiteIDResource())
Lookup.register(SourceResource())
Lookup.register(LutInterventionItnCoveragesAdmin1Resource())
Lookup.register(LutInterventionIrsCoveragesAdmin1Resource())
