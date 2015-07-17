from django.db import models

# Create your models here.
class CsvFileUpload(models.Model):
    dataType = models.CharField(max_length=20, choices=(('Humidity','Humidity (0-1)'), ('Rainfall','Rainfall (mm)'), ('Temperature','Temperature (C)')))
    csvFile = models.FileField(upload_to='documents/%Y/%m/%d')

class ClimateFilesUpload(models.Model):
    dataType = models.CharField(max_length=20, choices=(('Humidity','Humidity (0-1)'), ('Rainfall','Rainfall (mm)'), ('Temperature','Temperature (C)')))
    binFile = models.FileField(upload_to='documents/%Y/%m/%d')
    jsonFile = models.FileField(upload_to='documents/%Y/%m/%d')

class NodeLocationData(models.Model):
    nodeID = models.CharField(max_length=10)
    resolution = models.CharField(max_length=15)
    latitude = models.FloatField()
    longitude = models.FloatField()
    locationName = models.CharField(max_length=100)

# class ClimateFiles(models.Model):
#     humidityBinFile = models.FileField(upload_to='documents/%Y/%m/%d')#, name="Humidity Binary")
#     humidityJsonFile = models.FileField(upload_to='documents/%Y/%m/%d', name="Humidity Json")
#     rainfallBinFile = models.FileField(upload_to='documents/%Y/%m/%d', name="Rainfall Binary")
#     rainfallJsonFile = models.FileField(upload_to='documents/%Y/%m/%d', name="Rainfall Json")
#     temperatureBinFile = models.FileField(upload_to='documents/%Y/%m/%d', name="Temperature Binary")
#     temperatureJsonFile = models.FileField(upload_to='documents/%Y/%m/%d', name="Temperature Json")
#     demographicsFile = models.FileField(upload_to='documents/%Y/%m/%d', name="Demographics")
