########################################################################################################################
# VECNet CI - Prototype
# Date: 26/5/2014
# Institution: University of Notre Dame
# Primary Author:
#   Alexander Vyushkov <alexander.vyushkov@nd.edu>
########################################################################################################################
from django.contrib.gis.db import models
from django.db.models import Q
from data_services.models import DimLocation, DimUser

fact_prefix = 'fact_'
dimension_prefix = 'dim_'


class DimDate(models.Model):
    #id = models.IntegerField(primary_key=True)
    timestamp = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'dim_date'

    def __str__(self):
        return str(self.timestamp)


class DimSource(models.Model):
    #id = models.IntegerField(primary_key=True)
    source = models.CharField(max_length=255)
    file_uid = models.CharField(max_length=100)

    class Meta:
        db_table = 'dim_source'

class DimSubgroup(models.Model):
    #id = models.IntegerField(primary_key=True)
    subgroup = models.TextField()

    class Meta:
        db_table = 'dim_subgroup'


class LutMapSiteid(models.Model):
    #id = models.IntegerField()
    map_site_id = models.IntegerField()
    geom = models.PointField()
    objects = models.GeoManager()

    class Meta:
        db_table = 'lut_map_siteid'


class LutSpecies(models.Model):
    lookup = True
    # species_key = models.IntegerField(primary_key=True)
  #  location_key = models.ForeignKey(DimLocation, db_column='location_key')
  # source_key = models.IntegerField()
    species = models.CharField(max_length=255, blank=True)
    form = models.CharField(max_length=255, blank=True)
    vector_status = models.CharField(max_length=255, blank=True)
    daily_adult_survival_rate = models.CharField(max_length=255, blank=True)
    larval_survival_rate = models.CharField(max_length=255, blank=True)
    indoor_feeding_rate = models.CharField(max_length=255, blank=True)
    human_blood_index = models.CharField(max_length=255, blank=True)
    peak_biting_time = models.CharField(max_length=255, blank=True)
    length_of_feeding_cycle = models.CharField(max_length=255, blank=True)
    form_of_larval_habitat = models.CharField(max_length=255, blank=True)
    pre_feeding_resting_habits = models.CharField(max_length=255, blank=True)
    post_feeding_resting_habits = models.CharField(max_length=255, blank=True)
    flight_range = models.CharField(max_length=255, blank=True)
    sugar_meal_frequency = models.CharField(max_length=255, blank=True)
    sugar_sources = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'lut_species'
    def get_fields(self):
        return [(field.name, field.value_to_string(self)) for field in LutSpecies._meta.fields]
    def get_field(self, name):
        return getattr(self, name)

class LutIntervention(models.Model):
    #id = models.IntegerField(primary_key=True)
    source_key = models.ForeignKey(DimSource, db_column='source_key')
    intervention_name = models.TextField(blank=True)
    abbreviation = models.TextField(blank=True)
    description = models.TextField(blank=True)
    synonyms = models.TextField(blank=True)

    class Meta:
        db_table = 'lut_intervention'

class LutInterventionItnCoveragesAdmin1(models.Model):
    lookup = True
    gaul_code = models.IntegerField()   # GAUL code of the admin1 district (province, state etc)
    country = models.TextField()        # Country name
    province_name = models.TextField()  # Name of the admin1 district
    # The estimated percent of children under 5 year sleeping under a bednet
    percent_of_children_under_5_years_sleeping_under_a_bednet = models.FloatField(blank=True, null=True)
    the_estimated_percent_households_with_itn = models.FloatField(blank=True, null=True)  # The estimated percent of households with an insecticide-treated bednet
    percent_itn_all = models.FloatField(blank=True, null=True)       #
    year = models.IntegerField(blank=True, null=True)    # Year when ITN data was collected
    source = models.TextField()     # Source of the ITN data
    source_url = models.TextField(blank=True, null=True) # Link to ITN data source in the Digital Library

    class Meta:
        db_table = 'lut_intervention_itn_coverage_admin1'
        unique_together = ('country','province_name', "year")
    def get_fields(self):
        return [(field.name, field.value_to_string(self)) for field in LutInterventionItnCoveragesAdmin1._meta.fields]
    def get_field(self, name):
        return getattr(self, name)

class LutInterventionIrsCoveragesAdmin1(models.Model):
    lookup = True
    gaul_code = models.IntegerField()     # GAUL code of the admin1 district (province, state etc)
    country = models.TextField()          # Country name
    province_name = models.TextField()    # Name of the admin1 district
    percent_of_the_population_protected_by_irs = models.FloatField()  # The estimated percent of the population protected by IRS
    year = models.IntegerField()      # Year when IRS data was collected
    source = models.TextField()       # Source of the IRS data
    source_url = models.TextField(blank=True, null=True) # Link to IRS data source in the Digital Library

    class Meta:
        db_table = 'lut_intervention_irs_coverage_admin1'
        unique_together = ('country','province_name', "year")
    def get_fields(self):
        return [(field.name, field.value_to_string(self)) for field in LutInterventionIrsCoveragesAdmin1._meta.fields]
    def get_field(self, name):
        return getattr(self, name)

class LutEntomologicalEndpoint(models.Model):
    lookup = True
    #id = models.IntegerField(primary_key=True)
    #intervention_key = models.ForeignKey(LutIntervention, db_column='intervention_key')
    #source_key = models.ForeignKey(DimSource, db_column='source_key')
    paradigms = models.CharField(max_length=255, blank=True)
    product_description = models.TextField(blank=True)
    impact_human_landing_rates = models.CharField(max_length=255, blank=True)
    impact_direct_mortality = models.CharField(max_length=255, blank=True)
    impact_vector_mosquito_abundance_in_treated_area = models.CharField(max_length=255, blank=True)
    movement_away_from_a_point_source = models.CharField(max_length=255, blank=True)
    impact_rate_of_entry_into_treated_area = models.CharField(max_length=255, blank=True)
    impact_exit_rate_from_treated_area = models.CharField(max_length=255, blank=True)
    impact_percent_of_blood_fed = models.CharField(max_length=255, blank=True)
    impact_number_or_percent_of_blood_fed = models.CharField(max_length=255, blank=True)
    impact_sporozoite_rate = models.CharField(max_length=255, blank=True)
    impact_number_of_gravid_and_parous_females = models.CharField(max_length=255, blank=True)
    impact_rate_of_inhibition_of_adult_emergence = models.CharField(max_length=255, blank=True)
    #impact_larval_and_pupal_density = models.CharField(max_length=255, blank=True)
    #impact_lethality_to_f1_females = models.CharField(max_length=255, blank=True)
    possess_the_desired_trait = models.CharField(max_length=255, blank=True)
    establishment_within_a_cage_population = models.CharField(max_length=255, blank=True)
    mating_competitiveness = models.CharField(max_length=255, blank=True)
    duration_of_effective_life_or_replacement_time = models.CharField(max_length=255, blank=True)
    number_of_new_infections_among_human_cohort = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'lut_entomological_endpoint'
    def get_fields(self):
        return [(field.name, field.value_to_string(self)) for field in LutEntomologicalEndpoint._meta.fields]
    def get_field(self, name):
        return getattr(self, name)

class DimWeatherStation(models.Model):
    source_key = models.IntegerField()
    station_number = models.CharField(max_length=255, blank=True)
    station_name = models.CharField(max_length=255, blank=True)
    station_location = models.PointField(null=True, blank=True)
    objects = models.GeoManager()

    class Meta:
        db_table = 'dim_weather_station'

class DimType(models.Model):
    type = models.CharField(max_length=100)

    class Meta:
        db_table = 'dim_type'

class FactDemographics(models.Model):
    """
    Contains population data for a given time range, specified by start and end date.
    """
    start_date_key = models.ForeignKey(DimDate, db_column='start_date_key',
                                       related_name='FactDemographics_start_date_key')
    end_date_key = models.ForeignKey(DimDate, db_column='end_date_key', related_name='FactDemographics_end_date_key')
    location_key = models.ForeignKey(DimLocation, db_column='location_key')
    user_key = models.ForeignKey(DimUser, db_column='user_key')
    source_key = models.ForeignKey(DimSource, db_column='source_key')
    yrs_0_4 = models.IntegerField(null=True, blank=True)
    yrs_5_9 = models.IntegerField(null=True, blank=True)
    yrs_10_14 = models.IntegerField(null=True, blank=True)
    yrs_15_19 = models.IntegerField(null=True, blank=True)
    yrs_20_24 = models.IntegerField(null=True, blank=True)
    yrs_25_29 = models.IntegerField(null=True, blank=True)
    yrs_30_34 = models.IntegerField(null=True, blank=True)
    yrs_35_39 = models.IntegerField(null=True, blank=True)
    yrs_40_44 = models.IntegerField(null=True, blank=True)
    yrs_45_49 = models.IntegerField(null=True, blank=True)
    yrs_50_54 = models.IntegerField(null=True, blank=True)
    yrs_55_59 = models.IntegerField(null=True, blank=True)
    yrs_60_64 = models.IntegerField(null=True, blank=True)
    yrs_65_69 = models.IntegerField(null=True, blank=True)
    yrs_70_74 = models.IntegerField(null=True, blank=True)
    yrs_75_79 = models.IntegerField(null=True, blank=True)
    yrs_80plus = models.IntegerField(null=True, blank=True)

    class Meta:
        """
        Meta options for FactDemographics.
        """
        db_table = 'fact_demographics'


class FactPacrainRainfall(models.Model):
    beg_obs_date_key = models.IntegerField()
    end_obs_date_key = models.IntegerField()
    last_mod_date_key = models.IntegerField()
    length_of_obs = models.IntegerField(null=True, blank=True)
    rainfall_amount = models.FloatField(null=True, blank=True)
    data_flags = models.IntegerField(null=True, blank=True)
    record_ident = models.TextField(blank=True)
    user_key = models.IntegerField()
    source_key = models.IntegerField()
    location_key = models.IntegerField()

    class Meta:
        db_table = 'fact_pacrain_rainfall'


class FactWeather(models.Model):
    mean_temp = models.FloatField(null=True, blank=True)
    mean_temp_obs_cnt = models.IntegerField(null=True, blank=True)
    mean_dewpnt = models.FloatField(null=True, blank=True)
    mean_dewpnt_obs_cnt = models.IntegerField(null=True, blank=True)
    mean_sl_press = models.FloatField(null=True, blank=True)
    mean_sl_press_obs_cnt = models.IntegerField(null=True, blank=True)
    mean_station_press = models.FloatField(null=True, blank=True)
    mean_station_press_obs_cnt = models.IntegerField(null=True, blank=True)
    mean_vis = models.FloatField(null=True, blank=True)
    mean_vis_obs_cnt = models.IntegerField(null=True, blank=True)
    mean_wind_spd = models.FloatField(null=True, blank=True)
    mean_wind_spd_obs_cnt = models.IntegerField(null=True, blank=True)
    max_sus_wind_spd = models.FloatField(null=True, blank=True)
    max_wind_gust = models.FloatField(null=True, blank=True)
    max_temp = models.FloatField(null=True, blank=True)
    min_temp = models.FloatField(null=True, blank=True)
    total_precip = models.FloatField(null=True, blank=True)
    snow_depth = models.FloatField(null=True, blank=True)
    fog_ind = models.NullBooleanField(null=True, blank=True)
    rain_drizz_ind = models.NullBooleanField(null=True, blank=True)
    snow_ice_pell_ind = models.NullBooleanField(null=True, blank=True)
    hail_ind = models.NullBooleanField(null=True, blank=True)
    thunder_ind = models.NullBooleanField(null=True, blank=True)
    tornade_funnel_ind = models.NullBooleanField(null=True, blank=True)
    user_key = models.ForeignKey(DimUser, db_column='user_key')
    location_key = models.ForeignKey(DimLocation, db_column='location_key')
    date_key = models.ForeignKey(DimDate, db_column='date_key')
    weather_station_key = models.ForeignKey("DimWeatherStation", null=True, db_column='weather_station_key', blank=True)
    source_key = models.IntegerField()

    class Meta:
        db_table = 'fact_weather'


class FactWmrActOprtnlCvrg(models.Model):
    #id = models.IntegerField(primary_key=True)
    any_1st_trtmnt_crses_dlvrd_incldng_act = models.FloatField(null=True, blank=True)
    act_trtmnt_crses_dlvrd = models.FloatField(null=True, blank=True)
    pcnt_any_am_cvrg_total = models.FloatField(null=True, blank=True)
    pcnt_act_cvrg_total = models.FloatField(null=True, blank=True)
    location_key = models.ForeignKey(DimLocation, db_column='location_key')
    date_key = models.ForeignKey(DimDate, db_column='date_key', related_name='FactWmrActOprtnlCvrg_date_key')
    end_date_key = models.ForeignKey(DimDate, db_column='end_date_key',
                                     related_name='FactWmrActOprtnlCvrg_end_date_key')
    user_key = models.ForeignKey(DimUser, db_column='user_key')
    source_key = models.ForeignKey(DimSource, db_column='source_key')

    class Meta:
        db_table = 'fact_wmr_act_oprtnl_cvrg'


class FactWmrHhSurveys(models.Model):
    #id = models.IntegerField(primary_key=True)
    pcnt_hh_gte1_anet = models.FloatField(null=True, blank=True)
    pcnt_hh_gte1_etn = models.FloatField(null=True, blank=True)
    pcnt_hh_gte1_itn = models.FloatField(null=True, blank=True)
    pcnt_total_pop_itn = models.FloatField(null=True, blank=True)
    pcnt_chldrn_lt5_anet = models.FloatField(null=True, blank=True)
    pcnt_chldrn_lt5_etn = models.FloatField(null=True, blank=True)
    pcnt_chldrn_lt5_itn = models.FloatField(null=True, blank=True)
    pcnt_preg_anet = models.FloatField(null=True, blank=True)
    pcnt_preg_etn = models.FloatField(null=True, blank=True)
    pcnt_preg_itn = models.FloatField(null=True, blank=True)
    location_key = models.ForeignKey(DimLocation, db_column='location_key')
    date_key = models.ForeignKey(DimDate, db_column='date_key', related_name='FactWmrHhSurveys_date_key')
    end_date_key = models.ForeignKey(DimDate, db_column='end_date_key', related_name='FactWmrHhSurveys_end_date_key')
    source_key = models.ForeignKey(DimSource, db_column='source_key')
    subgroup_key = models.ForeignKey(DimSubgroup, db_column='subgroup_key')
    user_key = models.ForeignKey(DimUser, db_column='user_key')

    class Meta:
        db_table = 'fact_wmr_hh_surveys'


class FactWmrIrsOprtnlCvrg(models.Model):
    #id = models.IntegerField(primary_key=True)
    nmbr_protected_irs = models.FloatField(null=True, blank=True)
    pcnt_irs_cvrg = models.FloatField(null=True, blank=True)
    location_key = models.ForeignKey(DimLocation, db_column='location_key')
    date_key = models.ForeignKey(DimDate, db_column='date_key', related_name='FactWmrIrsOprtnlCvrg_date_key')
    end_date_key = models.ForeignKey(DimDate, db_column='end_date_key',
                                     related_name='FactWmrIrsOprtnlCvrg_end_date_key')
    user_key = models.ForeignKey(DimUser, db_column='user_key')
    source_key = models.ForeignKey(DimSource, db_column='source_key')

    class Meta:
        db_table = 'fact_wmr_irs_oprtnl_cvrg'


class FactWmrItnOprtnlCvrg(models.Model):
    #id = models.IntegerField(primary_key=True)
    nmbr_llin_sold_dlvrd = models.FloatField(null=True, blank=True)
    nmbr_itn_sold_dlvrd = models.FloatField(null=True, blank=True)
    nmbr_itn_and_llin_sold_dlvrd = models.FloatField(null=True, blank=True)
    pcnt_itn_cvrg = models.FloatField(null=True, blank=True)
    location_key = models.ForeignKey(DimLocation, db_column='location_key')
    date_key = models.ForeignKey(DimDate, db_column='date_key',
                                 related_name='FactWmrItnOprtnlCvrg_date_key')
    end_date_key = models.ForeignKey(DimDate, db_column='end_date_key',
                                     related_name='FactWmrItnOprtnlCvrg_end_date_key')
    user_key = models.ForeignKey(DimUser, db_column='user_key')
    source_key = models.ForeignKey(DimSource, db_column='source_key')

    class Meta:
        db_table = 'fact_wmr_itn_oprtnl_cvrg'


class FactGrossNationalIncome(models.Model):
    date_key = models.ForeignKey(DimDate, null=True, db_column='start_date_key', blank=True,
                                 related_name='FactGrossNationalIncome_date_key')
    end_date_key = models.ForeignKey(DimDate, null=True, db_column='end_date_key', blank=True,
                                     related_name='FactGrossNationalIncome_end_date_key')
    location_key = models.ForeignKey(DimLocation, null=True, db_column='location_key', blank=True)
    gross_national_income = models.DecimalField(null=True, max_digits=100, decimal_places=2, blank=True)
    user_key = models.ForeignKey(DimUser, db_column='user_key')

    class Meta:
        db_table = 'fact_gross_national_income'


class FactHouseholds(models.Model):
    number_of_houses = models.IntegerField(null=True, blank=True)
    location_key = models.ForeignKey(DimLocation, null=True, blank=True, db_column='location_key')
    subgroup_key = models.ForeignKey(DimSubgroup, null=True, db_column='subgroup_key', blank=True)
    date_key = models.ForeignKey(DimDate, null=True, db_column='start_date_key', blank=True,
                                 related_name='FactHouseholds_date_key')
    end_date_key = models.ForeignKey(DimDate, null=True, db_column='end_date_key', blank=True,
                                     related_name='FactHouseholds_end_date_key')
    source_key = models.ForeignKey(DimSource, null=True, db_column='source_key', blank=True)
    user_key = models.ForeignKey(DimUser, db_column='user_key')

    class Meta:
        db_table = 'fact_households'


class FutureDimLocation(models.Model):
    """
    This is the future incarnation of DimLocation.  When the data purge before 4/28/2014 happens, the database will
    be updated and all constraints currently pointing to DimLocation will be repaired and point here.
    """
    admin007 = models.CharField(max_length=255, null=True, blank=True)
    admin0 = models.CharField(max_length=255, null=True, blank=True)
    admin1 = models.CharField(max_length=255, null=True, blank=True)
    admin2 = models.CharField(max_length=255, null=True, blank=True)
    admin3 = models.CharField(max_length=255, null=True, blank=True)
    admin_level = models.IntegerField()
    geom_key = models.IntegerField()

    def __str__(self):
        return self.name()

    def name(self):
        """
        This creates a name for a particular instance of DimLocation
        """
        name = ''
        if self.admin007 and self.admin0:
            name += self.admin007 + ' - '
        if self.admin007 and not self.admin0:
            name += self.admin007
        if self.admin0:
            name += self.admin0
        if self.admin1:
            name += ', ' + self.admin1
        if self.admin2 and not self.admin1:
            name += ', ' + self.admin2
        if self.admin2 and self.admin1:
            name += ' ' + self.admin2
        if self.admin3:
            name += ' ' + self.admin3
        return name

    @classmethod
    def get_regions(cls):
        """
        Here we deliver a unique list of regions

        :returns: queryset containing distinct region names
        """
        return cls.objects.filter(admin_level=-1).distinct('admin007')

    @classmethod
    def get_countries(cls, region=None):
        """
        Here we get the countries for a particular region.

        If region is None, a complete list of countries is given.  Otherwise if region must be a string containing the
        region name.

        :param region: If None, returns all countries.  Allows the country search to be bounded by WHO region or list
                        of regions.
        :type region: str or list
        :returns: queryset containing countries
        :raises: TypeError if list of regions contains non-string or region is not None/list/str (or unicode)
        """
        if region is None:
            return cls.objects.filter(admin_level=0).distinct('admin0')
        elif isinstance(region, (str, unicode)):
            return cls.objects.filter(admin_level=0, admin007__iexact=region).distinct('admin0')
        elif isinstance(region, list):
            if all(map(lambda x: isinstance(x, (str, unicode)), region)):
                search_region = map(lambda x: Q(admin007__iexact=x), region)
                search_region = reduce(lambda a, b: a | b, search_region)
                return cls.objects.filter(admin_level=0).filter(search_region).distinct('admin0')
            else:
                raise TypeError("All elements in region list must be a string")
        else:
            raise TypeError("Region must be a string or list, received %s" % type(region))

    @classmethod
    def get_places_by_country(cls, country=None, **kwargs):
        """
        Here we get places within a county (like States within the United States) by country.

        If country is None, it will return a list of all places we have.  This is a big query as we do a distinct on it,
        so use sparingly.  Otherwise country can be a string or a list.

        Keywords further restricting this search are allowed.  Currently allowed keywords are admin007.  If
        a keyword not of the accepted type is give, a ValueError will be raised

        :param country: The country for which to get places
        :type country: str or list
        :returns: queryset containing places
        :raises: TypeError if country is not a list of strings or string (or unicode) or None
                ValueError if non-expected keyword is submitted
        """
        if country is None:
            qs = cls.objects.filter(admin_level=1)
        elif isinstance(country, (str, unicode)):
            qs = cls.objects.filter(admin_level=1, admin0__iexact=country)
        elif isinstance(country, list):
            if all(map(lambda x: isinstance(x, (str, unicode)), country)):
                country_search = map(lambda x: Q(admin0__iexact=x), country)
                country_search = reduce(lambda a, b: a | b, country_search)
                qs = cls.objects.filter(admin_level=1).filter(country_search)
            else:
                raise TypeError("All elements in country list must be a string")
        else:
            raise TypeError("Country must be a string or list, received %s" % type(country))

        allowed_keywords = ['admin007']
        if not cls.contains(kwargs.keys(), allowed_keywords):
            raise ValueError("Base keywords %s are allowed, received %s" % (allowed_keywords, kwargs.keys()))

        return qs.filter(**kwargs).distinct('admin1')

    @classmethod
    def get_places_by_admin1(cls, admin1=None, **kwargs):
        """
        Here we get places by admin1 (Like counties within states)

        If admin1 is None, this returns a list of unique place names.  This is a big query, as distinct is run on it, so
        use sparingly if admin1 is None.  Otherwise admin1 must be a string or list.

        Keywords for a query on this admin level are also allowed.  Allowed keywords are admin007, admin0.  Any others
        will result in a ValueError.

        :param admin1: Admin1 to search for places
        :type admin1: str or list
        :returns: queryset containing places for admin1
        :raises: TypeError if admin1 is not a str (or unicode), list, or None
                ValueError if keywords other than admin007 or admin0 are listed
        """
        if admin1 is None:
            qs = cls.objects.filter(admin_level=2)
        elif isinstance(admin1, (str, unicode)):
            qs = cls.objects.filter(admin_level=2, admin1__iexact=admin1)
        elif isinstance(admin1, list):
            if all(map(lambda x: isinstance(x, (str, unicode)), admin1)):
                admin1_search = map(lambda x: Q(admin1__iexact=x), admin1)
                admin1_search = reduce(lambda a, b: a | b, admin1_search)
                qs = cls.objects.filter(admin_level=2).filter(admin1_search)
            else:
                raise TypeError("All elements in admin1 list must be a string")
        else:
            raise TypeError("Admin1 must be a string or list, received %s" % type(admin1))

        allowed_kwargs = ['admin007', 'admin0']
        if not cls.contains(kwargs.keys(), allowed_kwargs):
            raise ValueError("Allowed base keywords are admin007 and admin0, received %s" % kwargs.keys())
        return qs.filter(**kwargs).distinct('admin2')

    @staticmethod
    def contains(l1, l2):
        """
        Helper function.
        Checks to see if a string from l2 is contained with all strings of l1
        """
        retbool = True
        for x in l1:
            retbool = retbool and any(map(lambda y: y in x, l2))

        return retbool

    class Meta:
        db_table = 'dim_locations_view'
        managed = False