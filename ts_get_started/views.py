from django.shortcuts import render, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.generic import TemplateView
from django.core.servers.basehttp import FileWrapper
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

import time
import datetime
from datetime import date, timedelta
import json
import random


class IndexView(TemplateView):
    template_name = 'ts_get_started/index.html'


class Modeling1View(TemplateView):
    template_name = 'ts_get_started/modeling1.html'


class Modeling2View(TemplateView):
    template_name = 'ts_get_started/modeling2.html'


class Modeling3View(TemplateView):
    template_name = 'ts_get_started/modeling3.html'


class Modeling4View(TemplateView):
    template_name = 'ts_get_started/modeling4.html'


class WeatherGeneratorView(TemplateView):
    template_name = 'ts_get_started/weatherGenerator.html'


def makeDates():
    fullStartDate = '2000' + '01' + '01'
    startDate = time.strptime(fullStartDate,'%Y%m%d')
    startDate = date(startDate.tm_year,startDate.tm_mon,startDate.tm_mday)
    dates = []
    dates.append(startDate.strftime('%m/%d/%Y'))
    for i in range(365):
        newDate = startDate + timedelta(i+1)
        dates.append(newDate.strftime('%m/%d/%Y'))

    return dates

def splitOptions(text):
    optionsSplit = text.split("&")

    options = {}

    for i in range(len(optionsSplit)):
        optionsSplit[i] = optionsSplit[i].split("=")
        options[optionsSplit[i][0]] = optionsSplit[i][1]

    return options

@never_cache
@csrf_exempt
def getTemperatureData(request):
    chartData = []
    count = 0
    dates = makeDates()

    data = makeTemperatureData(splitOptions(request.body))

    for dataPoint in data:
        chartData.append([])
        timeStamp = dates[count]
        timeStamp = time.mktime(datetime.datetime.strptime(str(timeStamp), "%m/%d/%Y").timetuple())*1000
        chartData[count].append(timeStamp)
        chartData[count].append(data[count])
        count += 1

    return HttpResponse(content=json.dumps(chartData), content_type='application/json')


def makeTemperatureData(options):
    chartData = []
    useCelcius = False

    for option in options:
        selection = options[option]

        if option == 'averageTemperature':
            if selection == 'low':
                baseValue = TEMP_BASE_LOW
            elif selection == 'medium':
                baseValue = TEMP_BASE_MID
            elif selection == 'high':
                baseValue = TEMP_BASE_HIGH
            else:
                raise ValueError('Bad averageTemperature selection')
        elif option == 'temperatureCurveType':
            if selection == 'softPeak':
                curve = TEMP_SOFT_MID_PEAK_CURVE
                variance = TEMP_SOFT_MID_PEAK_CURVE_VARIANCE
            elif selection == 'hardPeak':
                curve = TEMP_HARD_MID_PEAK_CURVE
                variance = TEMP_HARD_MID_PEAK_CURVE_VARIANCE
            elif selection == 'softValley':
                curve = TEMP_SOFT_MID_VALLEY_CURVE
                variance = TEMP_SOFT_MID_VALLEY_CURVE_VARIANCE
            elif selection == 'hardValley':
                curve = TEMP_HARD_MID_VALLEY_CURVE
                variance = TEMP_HARD_MID_VALLEY_CURVE_VARIANCE
            elif selection == 'flat':
                curve = TEMP_FLAT_CURVE
                variance = TEMP_FLAT_CURVE_VARIANCE
            else:
                raise ValueError('Bad temperatureCurveType selection')
        elif option == 'unitType':
            if selection == 'C':
                useCelcius = True

    monthTemperatureValues = generateMonthValues(curve, baseValue)

    chartData = generate1YearVariance(curve, variance, monthTemperatureValues)

    if (useCelcius):
        convertFahrenheitToCelcius(chartData)

    return chartData


@never_cache
@csrf_exempt
def getRainfallData(request):
    chartData = []
    count = 0
    dates = makeDates()

    data = makeRainfallData(splitOptions(request.body))

    for dataPoint in data:
        chartData.append([])
        timeStamp = dates[count]
        timeStamp = time.mktime(datetime.datetime.strptime(str(timeStamp), "%m/%d/%Y").timetuple())*1000
        chartData[count].append(timeStamp)
        chartData[count].append(data[count])
        count += 1

    return HttpResponse(content=json.dumps(chartData), content_type='application/json')


def makeRainfallData(options):
    chartData = []

    for option in options:
        selection = options[option]

        if option == 'averageRainfall':
            if selection == 'lowest':
                baseValue = PRECIPITATION_BASE_LOWEST
            elif selection == 'low':
                baseValue = PRECIPITATION_BASE_LOW
            elif selection == 'medium':
                baseValue = PRECIPITATION_BASE_MID
            elif selection == 'high':
                baseValue = PRECIPITATION_BASE_HIGH
            elif selection == 'highest':
                baseValue = PRECIPITATION_BASE_HIGHEST
            else:
                raise ValueError('Bad averageRainfall selection')
        elif option == 'rainfallCurveType':
            if selection == 'softPeak':
                curve = PRECIP_SOFT_MID_PEAK_CURVE
                variance = PRECIP_SOFT_MID_PEAK_CURVE_VARIANCE
            elif selection == 'hardPeak':
                curve = PRECIP_HARD_MID_PEAK_CURVE
                variance = PRECIP_HARD_MID_PEAK_CURVE_VARIANCE
            elif selection == 'softValley':
                curve = PRECIP_SOFT_MID_VALLEY_CURVE
                variance = PRECIP_SOFT_MID_VALLEY_CURVE_VARIANCE
            elif selection == 'hardValley':
                curve = PRECIP_HARD_MID_VALLEY_CURVE
                variance = PRECIP_HARD_MID_VALLEY_CURVE_VARIANCE
            elif selection == 'flat':
                curve = PRECIP_FLAT_CURVE
                variance = PRECIP_FLAT_CURVE_VARIANCE
            else:
                raise ValueError('Bad rainfallCurveType selection')

    monthRainfallValues = generateMonthValues(curve, baseValue)
    chartData = generate1YearPrecipitation(curve, variance, monthRainfallValues)

    print str(sum(chartData))

    return chartData


@never_cache
@csrf_exempt
def getHumidityData(request):
    chartData = []
    count = 0
    dates = makeDates()

    data = makeHumidityData(splitOptions(request.body))

    for dataPoint in data:
        chartData.append([])
        timeStamp = dates[count]
        timeStamp = time.mktime(datetime.datetime.strptime(str(timeStamp), "%m/%d/%Y").timetuple())*1000
        chartData[count].append(timeStamp)
        chartData[count].append(data[count])
        count += 1

    return HttpResponse(content=json.dumps(chartData), content_type='application/json')


def makeHumidityData(options):
    chartData = []
    curve = HUMIDITY_FLAT_CURVE
    variance = HUMIDITY_VARIANCE

    for option in options:
        selection = options[option]

        if option == 'averageHumidity':
            if selection == 'lowest':
                baseValue = HUMIDITY_BASE_LOWEST
            elif selection == 'low':
                baseValue = HUMIDITY_BASE_LOW
            elif selection == 'medium':
                baseValue = HUMIDITY_BASE_MID
            elif selection == 'high':
                baseValue = HUMIDITY_BASE_HIGH
            elif selection == 'highest':
                baseValue = HUMIDITY_BASE_HIGHEST
            else:
                raise ValueError('Bad averageHumidity selection')

    monthHumidityValues = generateMonthValues(curve, baseValue)
    chartData = generate1YearVariance(curve, variance, monthHumidityValues)

    return chartData










# The number of days in each month
JAN_DAYS = 31
FEB_DAYS = 28
MAR_DAYS = 31
APR_DAYS = 30
MAY_DAYS = 31
JUN_DAYS = 30
JUL_DAYS = 31
AUG_DAYS = 31
SEP_DAYS = 30
OCT_DAYS = 31
NOV_DAYS = 30
DEC_DAYS = 31

# Temperature curves             J    F    M    A    M    J    J    A    S    O    N    D
TEMP_FLAT_CURVE =            [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
TEMP_SOFT_MID_PEAK_CURVE =   [0.8, 0.8, 0.9, 1.0, 1.1, 1.2, 1.2, 1.2, 1.1, 1.0, 0.9, 0.8]
TEMP_HARD_MID_PEAK_CURVE =   [0.5, 0.6, 0.8, 1.0, 1.2, 1.4, 1.5, 1.4, 1.1, 0.9, 0.7, 0.5]
TEMP_SOFT_MID_VALLEY_CURVE = [1.2, 1.2, 1.2, 1.1, 1.0, 0.9, 0.8, 0.8, 0.8, 0.9, 1.0, 1.1]
TEMP_HARD_MID_VALLEY_CURVE = [1.4, 1.5, 1.4, 1.1, 0.9, 0.7, 0.5, 0.5, 0.6, 0.8, 1.0, 1.2]

# Rob's Curve
#TEMP_HARD_MID_PEAK_CURVE =   \
#    [0.333, 0.516, 0.650, 0.867, 1.083, 1.167, 1.267, 1.167, 1.100, 0.917, 0.833, 0.533]

# Base temperature variance values
TEMP_FLAT_CURVE_VARIANCE = 12
TEMP_SOFT_MID_PEAK_CURVE_VARIANCE = 15
TEMP_HARD_MID_PEAK_CURVE_VARIANCE = 30
TEMP_SOFT_MID_VALLEY_CURVE_VARIANCE = 15
TEMP_HARD_MID_VALLEY_CURVE_VARIANCE = 30

# Temperature base values in degrees Fahrenheit
TEMP_BASE_HIGH = 85
TEMP_BASE_MID = 60
TEMP_BASE_LOW = 35


# Precipitation curves
PRECIP_FLAT_CURVE =            [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
PRECIP_SOFT_MID_PEAK_CURVE =   [0.8, 0.8, 0.9, 1.0, 1.1, 1.2, 1.2, 1.2, 1.1, 1.0, 0.9, 0.8]
PRECIP_HARD_MID_PEAK_CURVE =   [0.5, 0.6, 0.8, 1.0, 1.2, 1.4, 1.5, 1.4, 1.2, 0.8, 0.7, 0.5]
PRECIP_SOFT_MID_VALLEY_CURVE = [1.2, 1.2, 1.2, 1.1, 1.0, 0.9, 0.8, 0.8, 0.8, 0.9, 1.0, 1.1]
PRECIP_HARD_MID_VALLEY_CURVE = [1.4, 1.5, 1.4, 1.1, 0.9, 0.7, 0.5, 0.5, 0.6, 0.8, 1.0, 1.2]

# Base precipitation variance values
PRECIP_FLAT_CURVE_VARIANCE = 12
PRECIP_SOFT_MID_PEAK_CURVE_VARIANCE = 15
PRECIP_HARD_MID_PEAK_CURVE_VARIANCE = 30
PRECIP_SOFT_MID_VALLEY_CURVE_VARIANCE = 15
PRECIP_HARD_MID_VALLEY_CURVE_VARIANCE = 30

# Precipitation base values in millimeters
PRECIPITATION_MULTIPLIER = 6.0
PRECIPITATION_BASE_HIGHEST = 2000.0 / 365.0 * PRECIPITATION_MULTIPLIER
PRECIPITATION_BASE_HIGH = 1500.0 / 365.0 * PRECIPITATION_MULTIPLIER
PRECIPITATION_BASE_MID = 1000.0 / 365.0 * PRECIPITATION_MULTIPLIER
PRECIPITATION_BASE_LOW = 500.0 / 365.0 * PRECIPITATION_MULTIPLIER
PRECIPITATION_BASE_LOWEST = 100.0 / 365.0 * PRECIPITATION_MULTIPLIER

# Percent chance that precipitation will occur
CHANCE_OF_LOW_PRECIPITATION = 100   # 78% chance to rain
CHANCE_OF_MID_PRECIPITATION = 22    # 15% chance to rain
CHANCE_OF_HIGH_PRECIPITATION = 7    # 7% chance to rain

# Amount that it will rain
PRECIPITATION_VARIANCE_MULTIPLIER_LOW = 0.25
PRECIPITATION_VARIANCE_MULTIPLIER_MID = 1.00
PRECIPITATION_VARIANCE_MULTIPLIER_HIGH = 1.50


# Humidity curves
HUMIDITY_FLAT_CURVE =            [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]

# Base humidity variance values
HUMIDITY_VARIANCE = 25

# Humidity base values in decimal percentages
HUMIDITY_BASE_HIGHEST = 0.9
HUMIDITY_BASE_HIGH = 0.7
HUMIDITY_BASE_MID = 0.5
HUMIDITY_BASE_LOW = 0.3
HUMIDITY_BASE_LOWEST = 0.1


def generateMonthValues(curve, baseValue):
    """Returns a list of values created by applying the curve to the base value.

    :param curve: a list containing values that represent a curve; values
                  represent a percentage where 0.8 = 80%
    :param baseValue: a base value multiplied to the curve; this value
                       represents an approximate mean value for the climate
                       variable being generated
    :return: a list of same size as the curve; values are created by multiplying
             the base_value to each of the initial curve values
    """
    monthValues = range(len(curve))
    for month in range(len(curve)):
        monthValues[month] = (curve[month] * baseValue)

    return monthValues


def generate1YearVariance(curve, variance, monthValues):
    """Returns a list filled with a year of stochastic data

    :param monthValues: a list of average monthly values for a given data set
    :param variance: the percentage variation in the daily values within a month
                     for 10% use: '10', not '0.1'
                     must be an integer
    :return a list filled with a year's worth of data
    """

    # create a list for the variance values
    varianceValues = []
    for value in range(len(curve)):
        varianceValues.append((1.0/curve[value]) * variance)

    previousDayValue = monthValues[0]


    # create lists for each month; lists contain data values generated
    # randomly based on the initial month values and specified variance
    january, previousDayValue = generate1MonthVariance(monthValues[0], varianceValues[0], JAN_DAYS, previousDayValue)
    february, previousDayValue = generate1MonthVariance(monthValues[1], varianceValues[1], FEB_DAYS, previousDayValue)
    march, previousDayValue = generate1MonthVariance(monthValues[2], varianceValues[2], MAR_DAYS, previousDayValue)
    april, previousDayValue = generate1MonthVariance(monthValues[3], varianceValues[3], APR_DAYS, previousDayValue)
    may, previousDayValue = generate1MonthVariance(monthValues[4], varianceValues[4], MAY_DAYS, previousDayValue)
    june, previousDayValue = generate1MonthVariance(monthValues[5], varianceValues[5], JUN_DAYS, previousDayValue)
    july, previousDayValue = generate1MonthVariance(monthValues[6], varianceValues[6], JUL_DAYS, previousDayValue)
    august, previousDayValue = generate1MonthVariance(monthValues[7], varianceValues[7], AUG_DAYS, previousDayValue)
    september, previousDayValue = generate1MonthVariance(monthValues[8], varianceValues[8], SEP_DAYS, previousDayValue)
    october, previousDayValue = generate1MonthVariance(monthValues[9], varianceValues[9], OCT_DAYS, previousDayValue)
    november, previousDayValue = generate1MonthVariance(monthValues[10], varianceValues[10], NOV_DAYS, previousDayValue)
    december, previousDayValue = generate1MonthVariance(monthValues[11], varianceValues[11], DEC_DAYS, previousDayValue)

    # concatenate the month lists into a year list
    year = january + february + march + april + may + june + july + august + \
           september + october + november + december

    return year


def generate1MonthVariance(baseValue, variance, numDays, previousDayValue):
    """Generate random values based on variance and value for a number of days

    :param baseValue: the base value to apply variance to
    :param variance: the percentage variation to apply to the base value
                     for 10% use: '10', not '0.1'
                     must be an integer
    :param numDays: the number of days to generate values for
    :return: a list of length numDays filled with values generated
             randomly based on the input value and variance
    """

    # create a list the for all of the days in the month
    month = range(numDays)

    maxVariance = baseValue + variance * 0.01 * baseValue
    minVariance = baseValue - variance * 0.01 * baseValue

    # for each day in the month, generate a random value
    # uniform(a, b) returns a random float N such that: a <= N <= b
    for day in month:
        if day % 3 == 0 and day != 0:
            previousDayValue = baseValue
            varianceToUse = variance / 2
        else:
            varianceToUse = variance / 4

        multiplier = random.uniform(-varianceToUse, varianceToUse) * 0.01
        month[day] = previousDayValue + previousDayValue * multiplier
        previousDayValue = month[day]

    return month, previousDayValue


def generate1YearPrecipitation(curve, variance, monthValues):
    """Returns a list filled with a year of stochastic data

    :param curve: a list containing values that represent a curve; values
                  represent a percentage where 0.8 = 80%
    :param variance: the percentage variation in the daily values within a month
                     for 10% use: '10', not '0.1'
                     must be an integer
    :param monthValues: a list of average monthly values for a given data set
    :return a list filled with a year's worth of data
    """

    # create a list for the variance values
    varianceValues = []
    for value in range(len(curve)):
        varianceValues.append((1.0/curve[value]) * variance)

    previousDayValue = monthValues[0]

    # create lists for each month; lists contain data values generated
    # randomly based on the initial month values and specified variance
    january, previousDayValue = generate1MonthPrecipitationVariance(monthValues[0], varianceValues[0], JAN_DAYS, previousDayValue)
    february, previousDayValue = generate1MonthPrecipitationVariance(monthValues[1], varianceValues[1], FEB_DAYS, previousDayValue)
    march, previousDayValue = generate1MonthPrecipitationVariance(monthValues[2], varianceValues[2], MAR_DAYS, previousDayValue)
    april, previousDayValue = generate1MonthPrecipitationVariance(monthValues[3], varianceValues[3], APR_DAYS, previousDayValue)
    may, previousDayValue = generate1MonthPrecipitationVariance(monthValues[4], varianceValues[4], MAY_DAYS, previousDayValue)
    june, previousDayValue = generate1MonthPrecipitationVariance(monthValues[5], varianceValues[5], JUN_DAYS, previousDayValue)
    july, previousDayValue = generate1MonthPrecipitationVariance(monthValues[6], varianceValues[6], JUL_DAYS, previousDayValue)
    august, previousDayValue = generate1MonthPrecipitationVariance(monthValues[7], varianceValues[7], AUG_DAYS, previousDayValue)
    september, previousDayValue = generate1MonthPrecipitationVariance(monthValues[8], varianceValues[8], SEP_DAYS, previousDayValue)
    october, previousDayValue = generate1MonthPrecipitationVariance(monthValues[9], varianceValues[9], OCT_DAYS, previousDayValue)
    november, previousDayValue = generate1MonthPrecipitationVariance(monthValues[10], varianceValues[10], NOV_DAYS, previousDayValue)
    december, previousDayValue = generate1MonthPrecipitationVariance(monthValues[11], varianceValues[11], DEC_DAYS, previousDayValue)

    # concatenate the month lists into a year list
    year = january + february + march + april + may + june + july + august + \
           september + october + november + december

    return year


def generate1MonthPrecipitationVariance(baseValue, variance, numDays, previousDayValue):
    """Generate random values based on variance and value for a number of days

    :param baseValue: the base value to apply variance to
    :param variance: the percentage variation to apply to the base value
                     for 10% use: '10', not '0.1'
                     must be an integer
    :param numDays: the number of days to generate values for
    :return: a list of length numDays filled with values generated
             randomly based on the input value and variance
    """

    # create a list the for all of the days in the month
    month = range(numDays)

    # in case we need it later
    previousDayValue = baseValue

    precipitationBase = 20
    precipitationChance = precipitationBase

    # for each day in the month, generate a random value
    # uniform(a, b) returns a random float N such that: a <= N <= b
    for day in month:

        #Modify the amount of variance in the rainfall
        varianceChance = random.randint(0,100)
        if varianceChance <= CHANCE_OF_HIGH_PRECIPITATION:
            heightAdjustment = PRECIPITATION_VARIANCE_MULTIPLIER_HIGH
        elif varianceChance <= CHANCE_OF_MID_PRECIPITATION:
            heightAdjustment = PRECIPITATION_VARIANCE_MULTIPLIER_MID
        else: # varianceChance <= CHANCE_OF_LOW_PRECIPITATION:
            heightAdjustment = PRECIPITATION_VARIANCE_MULTIPLIER_LOW

        multiplier = random.uniform(-variance, variance) * 0.01
        month[day] = (baseValue * heightAdjustment) + (baseValue * heightAdjustment * multiplier)
        chanceToRain = random.randint(0,100)

        if chanceToRain <= precipitationChance:
            precipitationChance = precipitationBase
        else:
            month[day] = 0
            precipitationChance += 2

    return month, previousDayValue


def convertFahrenheitToCelcius(temperatures):
    for temp in range(len(temperatures)):
        temperatures[temp] = (temperatures[temp] - 32) * 5/9


# useless function for now
def clamp(value, min_value, max_value):
    return max(min(value, max_value), min_value)