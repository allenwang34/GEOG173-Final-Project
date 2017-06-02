import arcpy                                                       
import os                                                               
from arcpy import env                                                 
import textwrap

# Define workspace as your folderpath
folder_path = r"E:\Geog173-Prog"
arcpy.env.workspace = folder_path
arcpy.env.overwriteOutput = True                        

# arcpy.mapping
mxd = arcpy.mapping.MapDocument(folder_path+"\Test1.mxd")  
df = arcpy.mapping.ListDataFrames(mxd)[0]
lyr_list = arcpy.mapping.ListLayers(mxd)
finalPDF_fname = folder_path +"/Mapbook.pdf"

if os.path.exists(finalPDF_fname):                                    
    os.remove(finalPDF_fname)  

for lyr in lyr_list:                                                   
    lyr.visible = True                                                  
    lyr.showLabels = False                                 

finalPDF = arcpy.mapping.PDFDocumentCreate(finalPDF_fname)   
tmpPDF = folder_path+"/tmp.pdf"                      

lyrlist = arcpy.mapping.ListLayers(mxd, "", df)[0]
stations = lyr_list[0]

#Text for title page
mapText = "Fuel Stations"+"\n\r" +"Number of Stations: "

elemlist = arcpy.mapping.ListLayoutElements(mxd)
title = elemlist[1]
title.text = mapText
arcpy.mapping.ExportToPDF(mxd, tmpPDF) 

# Get dataframe
df = arcpy.mapping.ListDataFrames(mxd)[0]
##df.extent = lyrExtent 

# Append multi-page PDF to finalMapPDF
finalPDF.appendPages(tmpPDF)

l=1
for lyr1 in lyr_list:
    print lyr1, "\t",l
    if l < 4:
        lyr1.visible = True
        lyr1.showLabels = True
    else:
        lyr1.visible = False
        lyr1.showLabels = False
    l = l+1

z=1  
# Get station cursor
for row in arcpy.da.SearchCursor(stations, ["SHAPE@", "FID","Station_Na","Street_Add","City","State","ZIP","Access_Day"]):
    
##    df.scale = df.scale * 1.1
    extent = row[0].extent
    df.extent = extent
    df.scale = 2000 #
    df.scale *= .4
    arcpy.RefreshActiveView()

    mapText = "Station #: "+ str(z) \
              +"\n" +textwrap.fill(row[2]) \
              + "\n" + row[3] +" " +row[4] +", "+ row[5] +" "+str(row[6]) \
              + "\nHours: " +  textwrap.fill(row[7])
    elemlist = arcpy.mapping.ListLayoutElements(mxd)
    title = elemlist[1]
    title.text = mapText

##    arcpy.mapping.ExportReport(stations,
##                           r"C:\Users\Frank\Google Drive\UCLA\Geog173_PythonForGIS\Final/Station_report.rlf",
##                          r"C:\Users\Frank\Google Drive\UCLA\Geog173_PythonForGIS\Final/tmp.pdf",
##                           "EXTENT",
##                           extent=df.extent)

    arcpy.mapping.ExportToPDF(mxd, tmpPDF)
    z=z+1

# Append multi-page PDF to finalMapPDF
    finalPDF.appendPages(tmpPDF)

finalPDF.saveAndClose()

del row, lyrlist, tmpPDF, df, lyr
del mxd, finalPDF, finalPDF_fname
print "Map book is finished"
