#Geog173 Group Project
#This script can help the user find three closest charing stations based on his or her current location.
#The result will be printed as a map book. On each map, we will include couple information about that charging station 

import arcpy
import math
import numpy
import os


#define workspace
folder_path = arcpy.GetParameterAsText(0)
arcpy.env.workspace = folder_path
arcpy.env.overwriteOutput = True

#choose a shapefile to workwith 
charging_stations = folder_path + r'\Charging_Stations.shp' 

#setup new file names and locations
charging_stations_copy = folder_path + r'\Results\Charging_Stations_Copy.shp'
single_point = folder_path + r'\Results\User Location.shp'
result_stations = folder_path + r'\Results\Nearest Stations.shp'

#copy the original file to two duplicated files 
arcpy.CopyFeatures_management(charging_stations, charging_stations_copy)
arcpy.CopyFeatures_management(charging_stations, result_stations)


#ask for user defined location
#sample location: x = -118.439298  y = 34.073990
userCoord = arcpy.GetParameterAsText(1) #get the user location 

#after user type in the xy location, extract x and y value 
Coords = userCoord.split(" ")
xCoord = float(Coords[0]) #make xy to float type
yCoord = float(Coords[1])

#make a tuple
xy = (xCoord,yCoord)

#create a point geometry in one of the duplicated file 
pointCursor = arcpy.da.InsertCursor(charging_stations_copy,["SHAPE@XY"])
pointCursor.insertRow([xy])
del pointCursor



#create a single point shapefile
arcpy.CopyFeatures_management(charging_stations_copy, single_point)

#remove extra rows from single_point shapefile
with arcpy.da.UpdateCursor(single_point,"Station_Na") as cursor:
    for row in cursor:
        if row[0] != " ":
            cursor.deleteRow()
del cursor, row

#remove the single point from the charging stations copy
with arcpy.da.UpdateCursor(charging_stations_copy,"Latitude") as cursor:
    for row in cursor:
        if row[0] == 0:
            cursor.deleteRow()
del cursor, row


#Let the user choose fuel type
fuelType = arcpy.GetParameterAsText(2)
originalStationFIDList = [] #we store the station fid values for that user defined type in a list

#we work on the original duplicated shapefile, only leave the user defined fuel type
with arcpy.da.UpdateCursor(charging_stations_copy,["Fuel_Type","FID"]) as cursor:
    for row in cursor:
        if row[0] != fuelType:#"BD","CNG","E85","HY","LNG","LPG"
            cursor.deleteRow()
        else:
            OriginalStationOID = row[1]
            originalStationFIDList.append(OriginalStationOID)

del cursor, row




#we condcut facility network analysis here
if arcpy.CheckExtension("NETWORK") == "Available":
    arcpy.CheckOutExtension("NETWORK")
else:
    quit()
   

inIncidents  = folder_path + r'\Results\User Location.shp'
inFacilities = folder_path + r'\Results\Charging_Stations_Copy.shp'

closest_layer = arcpy.MakeClosestFacilityLayer_na(in_network_dataset=folder_path + r'\Geog170_Street_Dataset\streets',
                                  out_network_analysis_layer="Closest Facility", impedance_attribute="Time", travel_from_to="TRAVEL_TO", default_cutoff="",
                                  default_number_facilities_to_find="3", accumulate_attribute_name="", UTurn_policy="ALLOW_UTURNS",
                                  restriction_attribute_name="TurnRestriction;OneWay", hierarchy="USE_HIERARCHY", hierarchy_settings="",
                                  output_path_shape="TRUE_LINES_WITH_MEASURES", time_of_day="", time_of_day_usage="NOT_USED")

out_CL = closest_layer.getOutput(0)

subLayerNames = arcpy.na.GetNAClassNames(out_CL)
facilitiesLayerName = subLayerNames["Facilities"]
incidentsLayerName = subLayerNames["Incidents"]

arcpy.na.AddLocations(out_CL,facilitiesLayerName,inFacilities,"","")
arcpy.na.AddLocations(out_CL,incidentsLayerName,inIncidents,"","")

out_layer = folder_path + r'\Results\OUTPUT_LAYER.lyr'



arcpy.na.Solve(out_CL,"SKIP")

out_CL.saveACopy(out_layer)


routesLayer = out_layer + r'\Closest Facility\Routes'
routesShape = folder_path + r'\Results\Routes.shp'

layerFile = arcpy.mapping.Layer(out_layer)
layers = arcpy.mapping.ListLayers(layerFile)

for layer in layers:
    if layer.name == "Routes":
        arcpy.CopyFeatures_management(layer, routesShape)



arcpy.CheckInExtension("NETWORK")

#Create a shapefile of selected stations from route shapefile

stationIndexList = [] 
stations = arcpy.SearchCursor(routesShape)

for station in stations:
    stationIndex = station.getValue("FacilityID")
    stationIndexList.append(stationIndex)

del stations, station

stationIndexList.sort()
 
targetStationIndexList = [] 
indexCounter = 0 
outerCounter = 0
for originalIndex in originalStationFIDList:
    realIndex = stationIndexList[indexCounter] -1
    if realIndex == outerCounter: 
        targetStationIndexList.append(originalIndex)
        if indexCounter < 2:
            indexCounter += 1
        else:
            break 
    outerCounter += 1

targetStationIndexList.sort()

counter = 0 
with arcpy.da.UpdateCursor(result_stations,"FID") as cursor:
    for row in cursor:
        if row[0] != targetStationIndexList[counter]: 
            cursor.deleteRow()
        else:
            if counter < 2:
                counter += 1
            else:
                counter = 2
del cursor, row

#Automatic add everything to the map
mxdFileLocation = r'E:\Final Project\FinalProject.mxd'
mxd = arcpy.mapping.MapDocument("CURRENT")
df = arcpy.mapping.ListDataFrames(mxd,"*")[0]

pointList = [routesShape,single_point,result_stations]

for point in pointList:
    newLayer = arcpy.mapping.Layer(point)
    arcpy.mapping.AddLayer(df,newLayer,"TOP")

mxd.save()


PDFName = folder_path + r'/Nearest Alternative Fuel Charging Stations.pdf'

myPDF = arcpy.mapping.PDFDocumentCreate(PDFName)
stationLyr = arcpy.mapping.ListLayers(mxd)[0]

#rows = arcpy.SearchCursor(routesShape)
#for row in rows:
    #stationNa = row.getValue()


arcpy.SelectLayerByAttribute_management(stationLyr, "NEW_SELECTION")
df.extent = stationLyr.getSelectedExtent()
df.scale *= 1.2
arcpy.RefreshActiveView()
arcpy.SelectLayerByAttribute_management(stationLyr,"CLEAR_SELECTION")
arcpy.mapping.ExportToPDF(mxd,PDFName, "PAGE_LAYOUT")




