
#define workspace
folder_path = arcpy.GetParameterAsText(0)
arcpy.env.workspace = folder_path
arcpy.env.overwriteOutput = True

###choose a shapefile to workwith 
charging_stations = folder_path + r'\Charging_Stations.shp' #this can be a feature class


#charging_stations = folder_path + r'\Charging_Stations.shp'
charging_stations_copy = folder_path + r'\Results\Charging_Stations_Copy.shp'
single_point = folder_path + r'\Results\Single_Point.shp'
result_stations = folder_path + r'\Results\Results_Stations.shp'

arcpy.CopyFeatures_management(charging_stations, charging_stations_copy)
arcpy.CopyFeatures_management(charging_stations, result_stations)

#xy = "34.073990,-118.439298" (SAMPLE COORDINATES)
userCoord = arcpy.GetParameterAsText(1) #get the user location 


Coords = userCoord.split(" ")
##the second index is north (x)
xCoord = float(Coords[0])
##the first index is west (y)
yCoord = float(Coords[1])
#make xy a float
xy = (xCoord,yCoord)

#create point cursor to add xy point to shapefile copy
pointCursor = arcpy.da.InsertCursor(charging_stations_copy,["SHAPE@XY"])
#insert point using cursor into shapefile
pointCursor.insertRow([xy])

del pointCursor

#create single point shapefile based off copy of shapefile
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


#get fuel type
fuelType = arcpy.GetParameterAsText(2)
originalStationFIDList = []

#cursor to select fuel type , will remove all fuel types that are not the selected fuel type
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
if arcpy.CheckExtension("Network") == "Available":
    arcpy.CheckOutExtension("Network")   

#create file path info for incidents and facilities
inIncidents  = folder_path + r'\Results\Single_Point.shp'
inFacilities = folder_path + r'\Results\Charging_Stations_Copy.shp'

#create a closest facility layer that
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

#folder path of routes to be used as the output shapefile for easy manipulation
routesShape = folder_path + r'\Results\Routes.shp'

#object to be used to select a layerfile
layerFile = arcpy.mapping.Layer(out_layer)
#object to be used to select a specific layer in the layerfile
layers = arcpy.mapping.ListLayers(layerFile)

#search through each sublayer and if sublayer is called routes
#create a shapefile of the sublayer
for layer in layers:
    if layer.name == "Routes":
        arcpy.CopyFeatures_management(layer, routesShape)

#check in the extension
arcpy.CheckInExtension("Network")
