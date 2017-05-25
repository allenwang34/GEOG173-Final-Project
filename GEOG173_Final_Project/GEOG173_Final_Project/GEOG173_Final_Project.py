#Geog173 Group Project
#This script can help the user find three closest charing stations based on his or her current location.
#The result will be printed as a map book. On each map, we will include couple information about that charging station 

import arcpy
import math
import numpy

define workspace
workspace = arcpy.GetParameterAsText(0)
arcpy.env.workspace = workspace
arcpy.env.overwriteOutput = True

###choose a shapefile to workwith 
inStations = arcpy.GetParameterAsText(1) #this can be a feature class
outStations = arcpy.GetParameterAsText(2) #this is a duplicated point layer, we will create user location on this layer
results = arcpy.GetParameterAsText(3) #This shape file only includes the result stations and their distances&travel time to the user.
#we will create map book from this result layer. 

#######################################
#           David's Code
#   ################################
#       Network Analyst Code
#
#######################################

#######################################
#           David's Code
#   ################################
#       Network Analyst Code
#
#######################################

folder_path = r'D:\Final Project Data'

charging_stations = folder_path + r'\Charging_Stations.shp'
charging_stations_copy = folder_path + r'\Charging_Stations_Copy.shp'
single_point = folder_path + r'\Single_Point.shp'

arcpy.CopyFeatures_management(charging_stations, charging_stations_copy)
###########################################
#   GETS THE XY INFO
###########################################

# ASK FOR X,Y I WILL PUT IN A PLACEHOLDER, just uncomment and delete placeholder
#xy = arcpy.GetParameterAsText(4)

#place_holder xy
xy = "34.073990,-118.439298"
#split the string
split_text = xy.split(",")
#the second index is north (x)
x = split_text[1]
#the first index is west (y)
y = split_text[0]

#make xy a float
xy = (float(x),float(y))

###########################################
#   Adds point to charging stations copy
###########################################

pointCursor = arcpy.da.InsertCursor(charging_stations_copy,["SHAPE@XY"])
pointCursor.insertRow([xy])

del pointCursor

###########################################
#   create single point shapefile
#   remove all extra points from shapefile
###########################################

#create single point shapefile
arcpy.CopyFeatures_management(charging_stations_copy, single_point)

#remove extra rows from single_point shapefile
with arcpy.da.UpdateCursor(single_point,"Latitude") as cursor:
    for row in cursor:
        if row[0] != 0:
            cursor.deleteRow()
del cursor

#remove the single point from the charging stations copy
with arcpy.da.UpdateCursor(charging_stations_copy,"Latitude") as cursor:
    for row in cursor:
        if row[0] == 0:
            cursor.deleteRow()
del cursor

#removes unlocated points from charging stations copy
with arcpy.da.UpdateCursor(charging_stations_copy,"FID") as cursor:
    for row in cursor:
        if row[0] == 6752:
            cursor.deleteRow()
        elif row[0] == 18104:
            cursor.deleteRow()
        elif row[0] == 23001:
            cursor.deleteRow()
        elif row[0] == 23002:
            cursor.deleteRow()
        elif row[0] == 23003:
            cursor.deleteRow()
del cursor

with arcpy.da.UpdateCursor(charging_stations_copy,"Fuel_Type") as cursor:
    for row in cursor:
        if row[0] != "HY":#"BD","CNG","E85","HY","LNG","LPG"
            cursor.deleteRow()
del cursor

###########################################
#   NETWORK ANALYST - TAKES APPROX 15 MIN
###########################################

print "STARTING THE NETWORK ANALYST"

#######################################
#           David's Code
#   ################################
#       Network Analyst Code
#
#######################################

if arcpy.CheckExtension("NETWORK") == "Available":
    arcpy.CheckOutExtension("NETWORK")
   

inIncidents  = folder_path + r'\Single_Point.shp'
inFacilities = folder_path + r'\Charging_Stations_Copy.shp'

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


out_layer = folder_path + r'\OUTPUT_LAYER.lyr'



print "SOLVING"

arcpy.na.Solve(out_CL,"SKIP")

print "FINISHED SOLVING"

print "SAVING"
out_CL.saveACopy(out_layer)

print "NEW SECTION"
routesLayer = out_layer + r'Closest Facility\Routes'
routesShape = folder_path + r'\Routes.shp'

layerFile = arcpy.mapping.Layer(out_layer)

layers = arcpy.mapping.ListLayers(layerFile)
for layer in layers:
    if layer.name == "Routes":
        arcpy.CopyFeatures_management(layer, routesShape)





##
##naClasses = arcpy.na.GetNAClassNames(out_CL)
##routes = arcpy.mapping.ListLayers(out_layer,naClasses["Routes"])[0]
##arcpy.management.CopyFeatures(routes,routesShape)

#copy output
arcpy.CopyFeatures_management(routesLayer, routesShape);

#arcpy.CopyFeatures_management(folder_path + r'\Closest Facility\Routes', routes);

# Replace a layer/table view name with a path to a dataset (which can be a layer file) or create the layer/table view within the script
# The following inputs are layers or table views: "Closest Facility\Routes"
arcpy.CopyFeatures_management(in_features="Closest Facility/Routes",out_feature_class="D:/Final Project Data/CopyRoutes.shp",config_keyword="#",spatial_grid_1="0",spatial_grid_2="0",spatial_grid_3="0")

print "FINISHED THE NETWORK ANALYST"

############################################



#The first step to do is let the user enter his or her location, X is longitude and Y is latitude. 
#Bascially we create a point geometry on the map. 




#The second step is to use network analysis to select the stations based on user input




#The third step is to create a new shapefile which only includes the selected charing stations. We add new fields to this new shapefile, distance and travel time. 




#The fourth step is to create a PDF map book based on the new shapefile we just created.
