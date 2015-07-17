from django.http import HttpResponse

from vecnet.emod import ClimateDataFile

from data_services.models import DimUser

from ts_emod2.models import Scenario

from datetime import date, timedelta, datetime
import time
import json


def get_weather_chart_data(request, scenario_id):
    dim_user = DimUser.objects.get(username=request.user.username)
    scenario = Scenario.objects.get(id=scenario_id)

    rainfall_bin = scenario.rainfall_bin_file.get_contents()
    rainfall_json = scenario.rainfall_json_file.get_contents()
    humidity_bin = scenario.humidity_bin_file.get_contents()
    humidity_json = scenario.humidity_json_file.get_contents()
    temperature_bin = scenario.temperature_bin_file.get_contents()
    temperature_json = scenario.temperature_json_file.get_contents()

    # Actual chart data
    weather_data = {}
    weather_data['rainfall'] = parse_weather_for_data(rainfall_json, rainfall_bin)
    weather_data['humidity'] = parse_weather_for_data(humidity_json, humidity_bin)
    weather_data['temperature'] = parse_weather_for_data(temperature_json, temperature_bin)

    # Weather info
    weather_data['name'] = 'test'

    return HttpResponse(content=json.dumps(weather_data))


def parse_weather_for_data(json_data, bin_data):
    climate_data_file = ClimateDataFile()
    climate_data_file.load(json_data, bin_data)

    # Retrieve all necessary data
    node_ids = climate_data_file.nodeIDs
    climate_data = climate_data_file.climateData
    start_day_of_year = climate_data_file.startDayOfYear
    data_value_count = climate_data_file.dataValueCount
    original_data_years = climate_data_file.originalDataYears

    # Fill dates
    months = ['', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
              'November', 'December']
    start_day_of_year_array = start_day_of_year.split(" ")
    for month in range(len(months)):
        if start_day_of_year_array[0] == months[month]:
            start_month = month
            break
    else:
        raise ValueError("Month name in StartDayOfYear must be in it's full name (ie January, not Jan or Jan.) "
                         "StartDayOfYear was " + start_day_of_year_array[0])
    start_year = original_data_years.split("-")[0] # Gets first year of year range (ie 1950 if it is 1950-2000)
    # This needs to be here to prevent it from incorrectly reading a date like 1955101 as 10/1/1955 instead of 1/01/1955
    if start_month < 10:
        start_month = "0" + str(start_month)
    full_start_date = str(start_year) + str(start_month) + str(start_day_of_year_array[1])
    start_date = time.strptime(full_start_date,'%Y%m%d')
    start_date = date(start_date.tm_year, start_date.tm_mon, start_date.tm_mday)
    dates = []
    dates.append(start_date.strftime('%m/%d/%Y'))
    for i in range(data_value_count-1):
        new_date = start_date + timedelta(i+1)
        dates.append(new_date.strftime('%m/%d/%Y'))

    # This packs everything into the form that highstocks is expecting
    node = []
    count = 0

    for data_point in climate_data[node_ids[0]]:
        node.append([])
        time_stamp = dates[count]
        time_stamp = time.mktime(datetime.strptime(str(time_stamp), "%m/%d/%Y").timetuple())*1000
        node[count].append(time_stamp)
        node[count].append(climate_data[node_ids[0]][count])
        count += 1

    return node