from django.shortcuts import render, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.generic import TemplateView
from django.core.servers.basehttp import FileWrapper
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from lib.templatetags.base_extras import set_notification

from .forms import EmodDownloadForm, CsvUploadForm, ClimateUploadForm
from .models import NodeLocationData
from vecnet.emod.climate import ClimateDataFile
from vecnet.emod.nodeid import nodeIDToLatLong, latLongToNodeID

import datetime
from datetime import date, timedelta
import time
import getpass
import json
import string

tempDir = settings.MEDIA_ROOT

class DateException(Exception):
    pass

class IndexView(TemplateView):
    template_name = 'ts_weather/index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['csvUploadForm'] = CsvUploadForm(prefix='csvUploadForm')
        context['climateUploadForm'] = ClimateUploadForm(prefix='climateUploadForm')
        return context

    def post(self, request):
        csvUploadForm = CsvUploadForm(prefix='csvUploadForm')
        climateUploadForm = ClimateUploadForm(prefix='climateUploadForm')
        action = self.request.POST['action']

        print("Before csv creation " + time.strftime("%M:%S"))
        if action == 'uploadCsv':
            csvUploadForm = CsvUploadForm(request.POST, request.FILES, prefix='csvUploadForm')
            if csvUploadForm.is_valid():
                try:
                    csvData, nodeIDs = self.getCsvDataFromCsv(request.FILES['csvUploadForm-csvFile'])
                except DateException as exception: # There was a bad date
                    set_notification('alert-error', 'File failed validation. ' + exception.message, self.request.session)
                    context = {
                        'csvUploadForm':     csvUploadForm,
                        'climateUploadForm': climateUploadForm,
                    }
                    return render(request, 'ts_weather/index.html', context)
                except: # There was an error with the files
                    set_notification('alert-error', 'File failed validation.', self.request.session)
                    context = {
                        'csvUploadForm':     csvUploadForm,
                        'climateUploadForm': climateUploadForm,
                    }
                    return render(request, 'ts_weather/index.html', context)
                dataTypeName = csvUploadForm['dataType'].value()
                context = {
                    'csvUploadForm':    csvUploadForm,
                    'csvData':          csvData,
                    'nodeIDs':          nodeIDs,
                    'dataTypeName':     dataTypeName,
                    'formType':         "emod",
                }
                return render(request, 'ts_weather/visualizer.html', context)
        elif action == 'uploadEmod':
            climateUploadForm = ClimateUploadForm(request.POST, request.FILES, prefix='climateUploadForm')
            if climateUploadForm.is_valid():
                jsonFile = request.FILES['climateUploadForm-jsonFile']
                binFile = request.FILES['climateUploadForm-binFile']
                print("After csv creation " + time.strftime("%M:%S"))
                try:
                    csvData, nodeIDs = self.getCsvDataFromEmod(jsonFile, binFile)
                except: # There was an error with the files
                    set_notification('alert-error', 'Files failed validation.', self.request.session)
                    context = {
                        'csvUploadForm':     csvUploadForm,
                        'climateUploadForm': climateUploadForm,
                    }
                    return render(request, 'ts_weather/index.html', context)
                print("After csv extraction " + time.strftime("%M:%S"))
                dataTypeName = climateUploadForm['dataType'].value()
                context = {
                    'climateUploadForm': climateUploadForm,
                    'csvData':           csvData,
                    'nodeIDs':           nodeIDs,
                    'dataTypeName':      dataTypeName,
                    'formType':          "csv",
                }
                return render(request, 'ts_weather/visualizer.html', context)
        return render(request, 'ts_weather/index.html', {}) # Just an error

    def getCsvDataFromEmod(self, jsonFile, binFile):
        print("Before climateDataFile creation " + time.strftime("%M:%S"))
        climateDataFile = ClimateDataFile()

        print("Before json lines " + time.strftime("%M:%S"))
        # Make string from the file (json)
        jsonLines = ""
        lines = iter(jsonFile)
        for line in lines:
            jsonLines += line

        print("Before bin lines " + time.strftime("%M:%S"))
        # Make string from the file (bin)
        binLines = ""
        lines = iter(binFile)
        for line in lines:
            binLines += line

        print("Before climateDataFile.load " + time.strftime("%M:%S"))
        climateDataFile.load(jsonLines, binLines)
        print("After climateDataFile.load " + time.strftime("%M:%S"))

        # Retrieve all necessary data
        nodeIDs = climateDataFile.nodeIDs
        climateData = climateDataFile.climateData
        startDayOfYear = climateDataFile.startDayOfYear
        dataValueCount = climateDataFile.dataValueCount
        originalDataYears = climateDataFile.originalDataYears
        metaData = {'idReference': climateDataFile.idReference, 'updateResolution': climateDataFile.updateResolution,
                    'dataProvenance': climateDataFile.dataProvenance}

        # Fill dates
        months = ['', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
                  'November', 'December']
        startDayOfYearArray = startDayOfYear.split(" ")
        for month in range(len(months)):
            if startDayOfYearArray[0] == months[month]:
                startMonth = month
                break
        else:
            raise ValueError("Month name in StartDayOfYear must be in it's full name (ie January, not Jan or Jan.) "
                             "StartDayOfYear was " + startDayOfYearArray[0])
        startYear = originalDataYears.split("-")[0] # Gets first year of year range (ie 1950 if it is 1950-2000)
        # This needs to be here to prevent it from incorrectly reading a date like 1955101 as 10/1/1955 instead of 1/01/1955
        if startMonth < 10:
            startMonth = "0" + str(startMonth)
        fullStartDate = str(startYear) + str(startMonth) + str(startDayOfYearArray[1])
        startDate = time.strptime(fullStartDate,'%Y%m%d')
        startDate = date(startDate.tm_year,startDate.tm_mon,startDate.tm_mday)
        dates = []
        dates.append(startDate.strftime('%m/%d/%Y'))
        for i in range(dataValueCount-1):
            newDate = startDate + timedelta(i+1)
            dates.append(newDate.strftime('%m/%d/%Y'))

        return json.dumps({'metaData': metaData, 'dates': dates, 'nodeIDs': nodeIDs, 'climateData': climateData}), nodeIDs




    def getCsvDataFromCsv(self, csvFile):
        dates = []
        nodes = {}

        # For info on iterators go to https://docs.python.org/2/tutorial/classes.html#iterators
        lines = iter(csvFile)
        headerRow1 = lines.next().strip('\n').strip('\r').split(',')
        metaData = {'idReference': headerRow1[0], 'updateResolution': headerRow1[1], 'dataProvenance': headerRow1[2]}
        # Split line into an array via ',' and remove \n and \r
        headerRow2 = lines.next().strip('\n').strip('\r').split(',')
        # Initialize each node's list, but -1 because of date col
        for col in range(len(headerRow2)-1):
            nodes[headerRow2[col+1]] = []
        # Get the rest of the rows
        for line in lines:
            row = line.strip('\n').strip('\r').split(',')
            if row[0] == '':
                raise DateException("Blank date given.")
            if not self.isValidDate(row[0]):
                raise DateException("Bad date of " + row[0])
            dates.append(row[0])

            # The -1 and +1 are to skip index 0, since it is for dates
            for col in range(len(headerRow2)-1):
                if col+1 > len(row) - 1 or row[col+1] == "":
                    nodes[headerRow2[col+1]].append(float(0))
                else:
                    nodes[headerRow2[col+1]].append(float(row[col+1]))
        csvFile.close()
        print("After csv main extraction " + time.strftime("%M:%S"))

        # Create node id list
        nodeIDs = []
        for node in nodes:
            nodeIDs.append(node)

        # Create climate data
        climateData = {}
        for node in nodes:
            climateData[node] = nodes[node]

        return json.dumps({'metaData': metaData, 'dates': dates, 'nodeIDs': nodeIDs, 'climateData': climateData}), nodeIDs


    def isValidDate(self, dateString):
        try:
            datetime.datetime.strptime(dateString, '%m/%d/%Y')
            return True
        except ValueError:
            return False
    


class VisualizeCsvView(TemplateView):
    template_name = "ts_weather/visualizer.html"

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['emodDownloadForm'] = EmodDownloadForm(prefix='emodDownloadForm')
        return context




class DownloadView(TemplateView):
    template_name = "ts_weather/download.html"

    def post(self, request, **kwargs):
        timeStamp = time.strftime("%H-%M-%S-%m-%d-%Y")
        downloadType = self.request.POST['downloadType']

        if downloadType == 'csv':
            extension = ".csv"
            theFile = self.makeCsvFile(request.POST['csvData'])
            contentType = 'application/csv'
        elif downloadType == 'emod':
            csvDataCleanJson = string.replace(request.POST['csvData'], '&quot;', '\"')
            print("After csvData string replace " + time.strftime("%M:%S"))
            csvData = json.loads(csvDataCleanJson)
            self.convertCsvToEmod(csvData, timeStamp)

            if 'binary' in request.POST['emodType']:
                extension = ".bin"
                fileName = tempDir + timeStamp + extension
                theFile = open(fileName, 'rb')
                contentType = 'application/octet-stream'
            elif 'json' in request.POST['emodType']:
                extension = ".json"
                fileName = tempDir + timeStamp + extension
                theFile = open(fileName, 'r')
                contentType = 'application/json'
                extension = ".bin.json"
            else:
                raise Exception('Missing extension')
        else:
            raise Exception('downloadType of ' + downloadType + ' is invalid and should either be emod or csv. '
                                                                '(Views:DownloadView:Post)')

        response = HttpResponse(FileWrapper(theFile), content_type=contentType)
        response['Content-Disposition'] = 'attachment; filename=' + request.POST['filePrefix'] + extension
        return response



    def makeCsvFile(self, csvDataJson):
        path = tempDir
        csvFileName = path + time.strftime("%H-%M-%S-%m-%d-%Y.csv")
        print("Before csvData string replace " + time.strftime("%M:%S"))
        csvDataCleanJson = string.replace(csvDataJson, '&quot;', '\"')
        print("After csvData string replace " + time.strftime("%M:%S"))
        csvData = json.loads(csvDataCleanJson)
        print("After csvData json.loads " + time.strftime("%M:%S"))

        # Retrieve all necessary data
        nodeIDs = csvData['nodeIDs']
        climateData = csvData['climateData']
        dates = csvData['dates']
        dataValueCount = len(csvData['climateData'][str(nodeIDs[0])])
        idReference = csvData['metaData']['idReference']
        updateResolution = csvData['metaData']['updateResolution']
        dataProvenance = csvData['metaData']['dataProvenance']

        # Fill header row 2
        headerRow2 = []
        headerRow2.append("Date")
        for node in nodeIDs:
            headerRow2.append(node)

        # Build lines
        lines = []
        # Add first line (metaData)
        line = idReference + "," + updateResolution + "," + dataProvenance + "\n"
        lines.append(line)
        # Add second line (header row 2)
        line = ""
        for item in headerRow2:
            line = line + str(item) + ","
        # Remove last "," and add "\n"
        tempLine = line.rsplit(",", 1)
        empty = ""
        line = empty.join(tempLine) + "\n"
        lines.append(line)
        # Add remaining lines
        for row in range(dataValueCount):
            line = dates[row] + ","
            for node in range(len(nodeIDs)):
                line = line + str(climateData[str(nodeIDs[node])][row]) + ","
            # Remove last "," and add "\n"
            tempLine = line.rsplit(",", 1)
            empty = ""
            line = empty.join(tempLine) + "\n"
            lines.append(line)

        # Write lines to file
        print("Before csv write " + time.strftime("%M:%S"))
        csvFile = open(csvFileName, 'w')
        for line in lines:
            csvFile.write(line)
        print("After csv write " + time.strftime("%M:%S"))

        csvFile.close()
        return open(csvFileName, 'r')



    def convertCsvToEmod(self, csvData, emodPrefix):
        path = tempDir
        binFileName = path + emodPrefix + ".bin"
        jsonFileName = path + emodPrefix + ".json"

        metaData = {}
        metaData['DateCreated'] = time.strftime("%m/%d/%Y")
        metaData['Tool'] = 'Csv to Emod Converter'
        metaData['Author'] = getpass.getuser()
        dates = csvData['dates']

        # Set nodeCount and dataValueCount
        metaData['NodeCount'] = len(csvData['climateData'])
        metaData['DatavalueCount'] = len(dates)

        # Determine and set startDayOfYear
        months = ['', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
                  'November', 'December']
        startDateArray = dates[0].split('/')
        startMonth = months[int(startDateArray[1])]
        startDayOfYear = startMonth + " " + startDateArray[0]
        metaData['StartDayOfYear'] = startDayOfYear

        # Determine and set originalDataYears
        startYear = startDateArray[2]
        endDateArray = dates[len(dates)-1].split('/')
        endYear = endDateArray[2]
        originalDataYears = str(startYear)
        if startYear != endYear:
            originalDataYears = originalDataYears + "-" + str(endYear)
        metaData['OriginalDataYears'] = originalDataYears

        # Get the remaining meta data
        metaData['IdReference'] = csvData['metaData']['idReference']
        metaData['UpdateResolution'] = csvData['metaData']['updateResolution']
        metaData['DataProvenance'] = csvData['metaData']['dataProvenance']

        climateDataFile = ClimateDataFile(metaData, csvData['nodeIDs'], csvData['climateData'])
        climateDataFile.save(jsonFileName, binFileName)
        return


@never_cache
@csrf_exempt
def getChartData(request, nodeID):
    print("Before csvData string replace " + time.strftime("%M:%S"))
    csvData = string.replace(request.body, '&quot;', '\"')
    print("After csvData string replace " + time.strftime("%M:%S"))
    csvData = json.loads(csvData)
    print("After csvData json.loads " + time.strftime("%M:%S"))

    node = []
    count = 0
    for dataPoint in csvData['climateData'][nodeID]:
        node.append([])
        timeStamp = csvData['dates'][count]
        timeStamp = time.mktime(datetime.datetime.strptime(str(timeStamp), "%m/%d/%Y").timetuple())*1000
        node[count].append(timeStamp)
        node[count].append(csvData['climateData'][nodeID][count])
        count = count+1
    print("After getChartData " + time.strftime("%M:%S"))
    return HttpResponse(content=json.dumps(node), content_type='application/json')


@never_cache
@csrf_exempt
def getLocationFromDatabase(request, resolution):
    nodeID = request.body

    try: # If the location is already in the database, retrieve the info
        nodeLocationData = NodeLocationData.objects.get(nodeID=nodeID, resolution=resolution)
        locationArray = []
        locationArray.append(nodeLocationData.latitude)
        locationArray.append(nodeLocationData.longitude)
        locationArray.append(nodeLocationData.locationName)
        location = locationArray
    except: # If the location is not in the database, determine latitude and longitude so we can send it to google
        latLong = []
        latitude, longitude = nodeIDToLatLong(nodeID, resolution)
        latLong.append(latitude)
        latLong.append(longitude)
        location = latLong

    return HttpResponse(content=json.dumps(location), content_type="text/plain")


@never_cache
@csrf_exempt
def addLocationToDatabase(request, nodeID):
    nodeLocationDataString = request.body
    nodeLocationDataDictionary = json.loads(nodeLocationDataString)
    nodeLocationData = NodeLocationData(nodeID=nodeID, resolution=nodeLocationDataDictionary['resolution'],
                                        latitude=nodeLocationDataDictionary['latitude'],
                                        longitude=nodeLocationDataDictionary['longitude'],
                                        locationName=nodeLocationDataDictionary['locationName'])
    nodeLocationData.save()

    return HttpResponse(content="Hi", content_type="text/plain")


def index(request):
    context = {}
    return render(request, 'ts_weather/index.html', context)
