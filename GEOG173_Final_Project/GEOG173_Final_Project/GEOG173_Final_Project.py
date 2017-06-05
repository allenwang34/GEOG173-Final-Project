#Geog173 Group Project
#This script can help the user find three closest charing stations based on his or her current location.
#The result will be printed as a map book. On each map, we will include couple information about that charging station 

import arcpy
import math
import numpy
import textwrap
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

#check out extension (although it does not currently work)
#you must manually select
arcpy.CheckOutExtension('Network')

   
#create file path info for incidents and facilities
inIncidents  = folder_path + r'\Results\User Location.shp'
inFacilities = folder_path + r'\Results\Charging_Stations_Copy.shp'

#create a closest facility layer
closest_layer = arcpy.MakeClosestFacilityLayer_na(in_network_dataset=folder_path + r'\Geog170_Street_Dataset\streets',
                                  out_network_analysis_layer="Closest Facility", impedance_attribute="Time", travel_from_to="TRAVEL_TO", default_cutoff="",
                                  default_number_facilities_to_find="3", accumulate_attribute_name="", UTurn_policy="ALLOW_UTURNS",
                                  restriction_attribute_name="TurnRestriction;OneWay", hierarchy="USE_HIERARCHY", hierarchy_settings="",
                                  output_path_shape="TRUE_LINES_WITH_MEASURES", time_of_day="", time_of_day_usage="NOT_USED")

#create a way to reference the closest facility layer
out_CL = closest_layer.getOutput(0)

#select the sublayers
subLayerNames = arcpy.na.GetNAClassNames(out_CL)
facilitiesLayerName = subLayerNames["Facilities"]
incidentsLayerName = subLayerNames["Incidents"]

#add facilities to facilities layer in the closest facility object layer
arcpy.na.AddLocations(out_CL,facilitiesLayerName,inFacilities,"","")
#add incidents to incidents layer in the closest facility object layer
arcpy.na.AddLocations(out_CL,incidentsLayerName,inIncidents,"","")

#create a folder path for the output of facilities layer
out_layer = folder_path + r'\Results\OUTPUT_LAYER.lyr'

#solve our closest facilities layer
#skip any errors
arcpy.na.Solve(out_CL,"SKIP")

#save a copy of our closest facility layer as a layerfile to our folder
out_CL.saveACopy(out_layer)

#object to be used to select a layerfile
routesShape = folder_path + r'\Results\Routes.shp'

#object to be used to select a specific layer in the layerfile
layerFile = arcpy.mapping.Layer(out_layer)
layers = arcpy.mapping.ListLayers(layerFile)

#search through each sublayer and if sublayer is called routes
#create a shapefile of the sublayer
for layer in layers:
    if layer.name == "Routes":
        arcpy.CopyFeatures_management(layer, routesShape)

#check in the extension
arcpy.CheckInExtension('Network')

################ DAVIDS COMMENTS END HERE ######################

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

############ EXTRA MAP BOOK CODE - LEAVE COMMENTED OUT ####################

###Create PDF Map Book
##
###setup PDF files
##PDFName = folder_path + r'/Nearest Alternative Fuel Charging Stations.pdf'
##myPDF = arcpy.mapping.PDFDocumentCreate(PDFName)
##tempPDF = arcpy.mapping.PDFDocumentCreate(folder_path+r'\temp.pdf')
##stationLyr = arcpy.mapping.ListLayers(mxd)[0]
##
##
###create a cover page
##
##title = arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT")[3]
##title.fontSize = 20
##title.text = "Nearest Alternative Fuel Stations"
##
##rows = arcpy.SearchCursor(result_stations)
##textCounter = 2
##stationCounter=1
##for row in rows:
##    stationNa = row.getValue("Station_Na")
##    texts = arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT")[textCounter]
##    texts.text = "Station {0}: {1}".format(stationCounter,stationNa)
##    texts.fontSize = 16 
##    textCounter -= 1
##    stationCounter += 1
##del row, rows, texts
##
##
##arcpy.SelectLayerByAttribute_management(stationLyr, "NEW_SELECTION")
##df.extent = stationLyr.getSelectedExtent()
##df.scale *= 1.2
##arcpy.RefreshActiveView()
##arcpy.SelectLayerByAttribute_management(stationLyr,"CLEAR_SELECTION")
##arcpy.mapping.ExportToPDF(mxd,folder_path+r'\temp.pdf', "PAGE_LAYOUT")
##myPDF.appendPages(folder_path+"\\temp.pdf")
##
##
###print a map book for each station
###use search cursor to go through each station
##stations = arcpy.SearchCursor(result_stations)
##texts = arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT")
##
###for each station zoom in and get all the needed information
##for station in stations:
##    fid = station.getValue("FID")
##    stationName = station.getValue("Station_Na")
##    stationAdd = station.getValue("Street_Add")
##    stationHr = station.getValue("Access_Day")
##    stationPay = station.getValue("Groups_Wit")
##    stationInfoList = ["Station {0}: {1}".format(fid+1, stationName),
##                    "Station Address: {}".format(stationAdd),
##                    "Station Hours: {}".format(stationHr),
##                    "Payment Method: {}".format(stationPay)]
##
##
###print out the station info into text elements 
##    counter = 3
##    for text in texts:
##        text.fontSize = 14
##        text.text = stationInfoList[counter]
##        counter -= 1
##
###zoom in to each station take a "screen shot" add to a temporary PDF. Then, append this tempoprary PDF to my map book.
##    arcpy.SelectLayerByAttribute_management(stationLyr, "NEW_SELECTION", "FID = {}".format(fid))
##    df.extent = stationLyr.getSelectedExtent(True)
##    df.scale *= 0.5
##    arcpy.RefreshActiveView()
##    arcpy.SelectLayerByAttribute_management(stationLyr,"CLEAR_SELECTION")
##    arcpy.mapping.ExportToPDF(mxd,folder_path+"\\temp.pdf","PAGE_LAYOUT")
##    myPDF.appendPages(folder_path+"\\temp.pdf")
## 
##
###save my map book.
##myPDF.saveAndClose()
##
##
###get rid of the temporary PDF file
##try: 
##    os.remove(folder_path+"\\temp.pdf")
##except OSError:
##    pass
###############################################################################################


############ KERNAL DENSITY  and MAP BOOK#######################################

PDFName = folder_path + r'\Nearest Alternative Fuel Charging Stations.pdf'

if os.path.exists(PDFName):                                            # Checks if file exists
    os.remove(PDFName)                                                # if so, it deletes file

# Create PDF mapbook
myPDF = arcpy.mapping.PDFDocumentCreate(PDFName)
stationLyr = arcpy.mapping.ListLayers(mxd)[0]

st_layers = arcpy.mapping.ListLayers(mxd)

# turn on only layers for first page, turn off the rest
counter = 1
for lyr in st_layers:
    if counter < 5:
        lyr.visible = True                                                        # to make all layers visible
        lyr.showLabels = True
    else:
        lyr.visible = False                                                        # to make all layers visible
    counter = counter +1

arcpy.SelectLayerByAttribute_management(stationLyr, "NEW_SELECTION")
df.extent = stationLyr.getSelectedExtent()
df.scale *= .1
arcpy.RefreshActiveView()
arcpy.SelectLayerByAttribute_management(stationLyr,"CLEAR_SELECTION")

# Print titles on first page
mapText = "3 Nearest Alternative Fuel Stations"+"\n\r" +"Type of Fuel: "+ fuelType
tmpPDF = folder_path+ r'\tmp.pdf'
elemlist = arcpy.mapping.ListLayoutElements(mxd)
title = elemlist[2]
title.text = mapText
arcpy.mapping.ExportToPDF(mxd, tmpPDF)

##****************************************
df_layers = arcpy.mapping.ListLayers(mxd)

# Turn off .tif layers and all labels
counter = 1
for lyr in df_layers:
    if counter < 5:
        lyr.visible = True                                                        # to make all layers visible
        lyr.showLabels = False
    else:
        lyr.visible = False
    counter = counter +1
    
newstations = df_layers[0]

# Get dataframe
df = arcpy.mapping.ListDataFrames(mxd)[0]

# Append multi-page PDF to finalMapPDF
myPDF.appendPages(tmpPDF)

# Turn off .tif layers
l=1
for lyr1 in df_layers:
    print lyr1, "\t",l
    if l == 1 or l == 2 or l == 3 or l == 4:
        lyr1.visible = True
        lyr1.showLabels = True
    else:
        lyr1.visible = False
    l = l+1

z=1  
# Get station cursor
for row in arcpy.da.SearchCursor(newstations, ["SHAPE@", "FID","Station_Na","Street_Add","City","State","ZIP","Access_Day"]):

# Set extent for 3 station pages    
    extent = row[0].extent
    df.extent = extent
    df.scale = 8000 #
    arcpy.RefreshActiveView()

# Print titles on each page
    mapText = "Station #: "+ str(z) \
              +"\n" +textwrap.fill(row[2]) \
              + "\n" + row[3] +" " +row[4] +", "+ row[5] +" "+str(row[6]) \
              + "\nHours: " +  textwrap.fill(row[7])
    elemlist = arcpy.mapping.ListLayoutElements(mxd)
    title = elemlist[2]
    title.text = mapText
    arcpy.mapping.ExportToPDF(mxd, tmpPDF)
    z=z+1

#Append multi-page PDF to finalMapPDF
    myPDF.appendPages(tmpPDF)

# Turn on only kernal density page and north america map
counter = 1
for lyr2 in df_layers:
    if counter > 4 and counter < 7:
        lyr2.visible = True                                                        # to make all layers visible
    else:
        lyr2.visible = False
    counter = counter + 1

arcpy.CheckOutExtension('Spatial')
OutputKernel = folder_path + "\FuelTypeKernel.tif"
arcpy.gp.KernelDensity_sa(charging_stations_copy, "NONE", \
                          OutputKernel,\
                          "0.1857694464", "", "SQUARE_MAP_UNITS",\
                          "DENSITIES", "PLANAR")
addlayer = arcpy.mapping.Layer(OutputKernel)
arcpy.mapping.AddLayer(df, addlayer)
arcpy.ApplySymbologyFromLayer_management("FuelTypeKernel.tif", "Kernel.tif")

# Set extent for Kernal Density page to always include complete USA
NewExtent = df.extent
NewExtent.XMin, NewExtent.YMin = -124.8, 26.0
NewExtent.XMax, NewExtent.YMax = -66.6, 49.0
df.extent = NewExtent

# Print title for Kernal density page
mapText = "Kernal Density Map of USA for "+ fuelType
tmpPDF = folder_path+ r'\tmp.pdf'
elemlist = arcpy.mapping.ListLayoutElements(mxd)
title = elemlist[2]
title.text = mapText
df.scale = df.scale *1.1

# Add page to PDF
arcpy.RefreshActiveView()
arcpy.mapping.ExportToPDF(mxd, tmpPDF)
myPDF.appendPages(tmpPDF)
arcpy.CheckInExtension('Spatial')

# Complete PDF and save
myPDF.saveAndClose()

del row, lyr
del mxd










