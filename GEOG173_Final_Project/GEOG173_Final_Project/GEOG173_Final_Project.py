#Geog173 Group Project
#This script can help the user find three closest charing stations based on his or her current location.
#The result will be printed as a map book. On each map, we will include couple information about that charging station 

import arcpy
import math

#define workspace
workspace = arcpy.GetParameterAsText(0)

arcpy.env.workspace = workspace
arcpy.env.overwriteOutput = True

#choose a shapefile to workwith 
inStations = arcpy.GetParameterAsText(1) #this can be a feature class
outStations = arcpy.GetParameterAsText(2) #this is a duplicated point layer, we will create user location on this layer
#results = arcpy.GetParameterAsText(3) #This shape file only includes the result stations and their distances&travel time to the user.
#we will create map book from this result layer. 



#The first step to do is let the user enter his or her location, X is longitude and Y is latitude. 
#Bascially we create a point geometry on the map. 
arcpy.CopyFeatures_management(inStations, outStations)
userCoord = arcpy.GetParameterAsText(3) #get the user location 
Coords = userCoord.split(" ")
xCoord = float(Coords[0])
yCoord = float(Coords[1])

cursor = arcpy.da.InsertCursor(outStations,["SHAPE@XY"])
xy = (xCoord,yCoord)
cursor.insertRow([xy])
del cursor

infoInserter = arcpy.da.UpdateCursor(outStations,["Station_Na","Latitude","Longitude"])
points = arcpy.SearchCursor(outStations)

for point in points:
    pointNam = point.getValue("Station_Na")
    if pointNam == " ":
        pointIndex = point.getValue("FID")

rowCounter = 0
for row in infoInserter:
    if rowCounter == pointIndex:
        row[0] = "UserLocation"
        row[1] = yCoord
        row[2] = xCoord
        infoInserter.updateRow(row)
        break
    rowCounter += 1

del points,point,infoInserter,row





#The second step is to use network analysis to select the stations based on user input




#The third step is to create a new shapefile which only includes the selected charing stations. We add new fields to this new shapefile, distance and travel time. 




#The fourth step is to create a PDF map book based on the new shapefile we just created.