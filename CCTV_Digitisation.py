#-------------------------------------------------------------------------------
# Name:        CCTV Automation
# Purpose:
# Updates:
#
# Author:      James.Runnalls
#
# Created:     06/07/2016
# Copyright:   (c) James.Runnalls 2016
# Licence:     <your licence>
#-------------------------------------------------------------------------------

print "Loading user interface"

# Import relevant modules
import csv, math, sys, shapefile
import Tkinter as t
import tkFileDialog as tf
import tkMessageBox as tm
import os
import xml.etree.ElementTree as ET
import shutil
import re

# Sets up user interface
window = t.Tk()
window.title('CCTV Automation')

# Function for inputting infiltration
def infil(h):
    INF = t.Tk()
    INF.title('Infiltration Entry')
    textin = "Input infiltration (l/s) seen at distance "+ h +"  "
    # This section builds the user interface
    # This is the first row for inputting the csv file location
    eih = t.StringVar()
    ehi1 = t.Message(text = textin,width=300)
    ehi2 = t.Entry(window, textvariable=eih,width=80)
    ehi3 = t.Button(text ="Enter", command = exchange)
    ehi2.textvariable = eih
    # This controls the layout of the user interface
    ehi1.grid(row=0, column=0, padx=5, pady=5)
    ehi2.grid(row=0, column=1, padx=5, pady=5)
    ehi.grid(row=0, column=2, padx=5, pady=5)
    # This opens the user interface
    INF.mainloop()

def exchange():
    inf = ehi2.get()
    INF.destry()
    return inf

# Function for locating files
def openfld():
    fldinput = tf.askdirectory()
    fld.set(fldinput)
    window.update_idletasks()

# Function for locating the save area
def saveas():
    saveasinput = tf.asksaveasfilename()
    osvv.set(saveasinput)
    window.update_idletasks()

# The main function
def main():
    window.update_idletasks()
    Folder = fld2.get()
    save = osv2.get()
    infl = var.get()
    window.destroy()
    try:

        print "Finding XML file"

        # Find xml file
        for root, dirs, files in os.walk(Folder):
            for file in files:
                if "Project.xml" in file:
                     xml = os.path.join(root, file)
                     break
            else:
                continue
            break

        # Open xml file
        tree = ET.parse(xml)
        root2 = tree.getroot()

        os.makedirs(save)

        # Set Name
        x = []
        for x in root2.iter('P_Name'):
            P_Name = str(x.text)
        for x in root2.iter('P_Date'):
            P_Date = str(x.text)
        Name = P_Name + " " + P_Date
        Name = re.sub(r'[^\w]', ' ', Name)

        outputfiles = save + "/" + Name

        print "Compiling S_T Matrix"

        # Compile S_T matrix
        S_T = []
        S_Tnodes = ['S_ID','S_PipeMaterial','S_PipeShape','S_PipeDia']
        for k in range(len(S_Tnodes)):
            x = []
            for n in root2.iter(S_Tnodes[k]):
                x.append(n.text)
            S_T.append(x)

        # Add SI_T information to matrix
        SI_Tnodes = ['SI_ID','SI_Weather','SI_InspectionStartTime','SI_InspDate']         # Elements to read from xml file
        SI_Index = []                                                       # Set up index variable
        S_ID = S_T[0][:]                                                    # Slice first column to get just S_ID
        for n in root2.iter('SI_Section_ID'):                                # Iterate through each of the SI_Section_ID values
            SI_Index.append(S_ID.index(n.text))                             # Asign an index to make sure that the two matrices are combined with the correct pipe information

        for k in range(len(SI_Tnodes)):                                     # Loop through each of the elements
            xx = [0.0] * (len(S_ID))                                        # Set up variable
            i = 0                                                           # Start counter
            for n in root2.iter(SI_Tnodes[k]):                               # Loop for each of the element names
                l = SI_Index[i]                                             # Find the index for each value within the element
                xx[l] = n.text                                              # Set the value from the xml at this index in variable xx
                i = i + 1                                                   # Increase counter
            S_T.append(xx)                                                  # Append xx to the main list of lists

        # Add start and end manholes
        xs = [0.0] * (len(S_ID))                                        # Set up variable
        xe = [0.0] * (len(S_ID))
        i = 0                                                           # Start counter
        for n in root2.iter('SI_InspectionDir'):                             # Loop for each of the element names
            l = SI_Index[i]
            kk = n.text
            kj = kk.split( )                                             # Find the index for each value within the element
            xs[l] = kj[0]
            xe[l] = kj[2]                                              # Set the value from the xml at this index in variable xx
            i = i + 1                                                   # Increase counter
        S_T.append(xs)                                                  # Append xx to the main list of lists
        S_T.append(xe)

        SO_Position = []
        for n in root2.iter('SO_Position'):
            SO_Position.append(n.text)

        print "Locating Video Files"

        # Add video name to the matrix
        SO_ClipFlag1 = []
        SO_Inspecs_ID = []
        SO_ClipFileName1 = []
        Vid = []
        SO_II = []
        SI_ID = S_T[4][:]
        for n in root2.iter('SO_ClipFlag1'):
            SO_ClipFlag1.append(n.text)
        for n in root2.iter('SO_ClipFileName1'):
            Vid.append(n.text)
        for root, dirs, files in os.walk(Folder):
            for name in files:
                if name.endswith(".mpg"):
                    for x in range(len(Vid)):
                        if Vid[x] == name:
                            Vid[x] = os.path.join(root, name)
        for n in root2.iter('SO_Inspecs_ID'):
            SO_Inspecs_ID.append(n.text)
        for k in range(len(SO_ClipFlag1)):
            if SO_ClipFlag1[k] != '0':
                SO_II.append(SO_Inspecs_ID[k])
        for k in range(len(SI_ID)):
            x = SO_II.index(SI_ID[k])
            SO_ClipFileName1.append(Vid[x])
        S_T.append(SO_ClipFileName1)

        print "Reading Manholes from Shapefile"

        # Search for manhole co-ordinates
        manholeFC = r"\\global\europe\Cardiff\Jobs\239000\239755-00\4 Internal Project Data\4-40 Calculations\CCTV Automation\Shapefile\ChamberAll.csv"
        S_StartNode = S_T[8][:]
        S_EndNode = S_T[9][:]
        mXS = ["0"] * len(S_StartNode)
        mXE = ["0"] * len(S_StartNode)
        mYS = ["0"] * len(S_StartNode)
        mYE = ["0"] * len(S_StartNode)
        with open(manholeFC) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                for k in range(len(S_StartNode)):
                    StartNode = S_StartNode[k].upper() # Make sure is upper case
                    EndNode = S_EndNode[k].upper()
                    if str(StartNode) == str(row['Manhole']):
                        # Assign startnode X and Y
                        mXS[k] = float(row['Xcoord'])
                        mYS[k] = float(row['Ycoord'])
                    if str(EndNode) == str(row['Manhole']):
                        # Assign endnode X and Y
                        mXE[k] = float(row['Xcoord'])
                        mYE[k] = float(row['Ycoord'])

        # Print out the manholes that cannot be found.
        for k in range(len(S_StartNode)):
            if mXS[k] == "0" and mXE[k] == "0":
                print "The manholes " + S_StartNode[k] + " and " + S_EndNode[k] + " could not be located in order to project the defects between them."
            if mXS[k] == "0" and mXE[k] != "0":
                print "The starting manhole " + S_StartNode[k] + " could not be located in order to project defects on the run towards manhole " + S_EndNode[k]
            if mXS[k] != "0" and mXE[k] == "0":
                print "The end manhole " + S_EndNode[k] + "could not be located in order to project defects on the run from manhole " + S_EndNode[k]

        print "Compiling SO_T Matrix (Locating photos and calculating geometry)"

        # Compile SO_T matrix for easy columns
        SO_T = []
        SO_Tnodes = ['SO_Inspecs_ID','SO_Position','SO_OpCode','SO_Text','SO_MPEGPosition','SO_Rate','SO_Value1','SO_Remark']
        for h in range(len(SO_Tnodes)):
            x = []
            for k in root2.findall('SO_T'):
                try:
                    x.append(k.find(SO_Tnodes[h]).text)
                except:
                    x.append('0')
                    pass
            SO_T.append(x)

        # Compile SO_T matrix for photos
        x = []
        for k in root2.findall('SO_T'):
            try:
                l = k.find('SO_PhotoFilename1').text
                # Find photo file
                for root, dirs, files in os.walk(Folder):
                    for file in files:
                        if l in file:
                             l2 = os.path.join(root, file)
                             break
                    else:
                        continue
                    break
                x.append(l2)
            except:
                x.append('0')
                pass
        SO_T.append(x)

        # Calculate geometry of each point
        z = 0
        a = []
        XS = []
        YS = []
        XE = []
        YE = []
        Startnode = []
        Endnode = []
        Material = []
        Shape = []
        Diameter = []
        Weather = []
        Starttime = []
        Date = []
        Video = []
        INF = []
        ycoord = []
        xcoord = []

        SO_OpCode = SO_T[2][:]
        for k in range(len(SO_OpCode)):
            z = SO_Position[k]
            a = SI_ID.index(SO_Inspecs_ID[k])
            XS = mXS[a]
            YS = mYS[a]
            XE = mXE[a]
            YE = mYE[a]

            if XS == "0" or YS == "0" or XE == "0" or YE == "0":
                ycoord.append("0")
                xcoord.append("0")
            else:
                # Calculate y
                y = float(z)* math.sin(math.atan(math.fabs((YE-YS)/(XE-XS))))
                # Calculate coordinate
                if YE >YS:
                    ycoord.append(YS+y)
                else:
                    ycoord.append(YS-y)

                # Calcaulte x
                x = float(z)* math.cos(math.atan(math.fabs((YE-YS)/(XE-XS))))
                # Calculcate coordinate
                if XE >XS:
                    xcoord.append(XS+x)
                else:
                    xcoord.append(XS-x)

            # Add attributtes

            Material.append(S_T[1][a])
            Shape.append(S_T[2][a])
            Diameter.append(S_T[3][a])
            Weather.append(S_T[5][a])
            Starttime.append(S_T[6][a])
            Date.append(S_T[7][a])
            Startnode.append(S_T[8][a])
            Endnode.append(S_T[9][a])
            Video.append(S_T[10][a])


        # Append to overall
        SO_T.append(Startnode)
        SO_T.append(Endnode)
        SO_T.append(Material)
        SO_T.append(Shape)
        SO_T.append(Diameter)
        SO_T.append(Weather)
        SO_T.append(Starttime)
        SO_T.append(Date)
        SO_T.append(Video)

        # Infiltration section
        SO_Text = SO_T[3][:]
        for k in range(len(SO_OpCode)):
            if infl == 1:
                if "Infiltration" in SO_Text[k]:
                    exist = os.path.isfile(SO_T[17][k])
                    if exist == True:
                        os.startfile(SO_T[17][k])
                        h = str(SO_T[1][k])
                        inf = raw_input("Input infiltration (l/s) seen at distance "+str(SO_T[1][k])+"  ")
                    else:
                        inf = 0.00
                else:
                    inf = 0.00
            else:
                inf = 0.00
            INF.append(inf)
        SO_T.append(INF)

        SO_T.append(xcoord)
        SO_T.append(ycoord)

        # Add format to columns
        SO_T[0].insert(0,'{00000000-0000-0000-0000-000000000000}')
        SO_T[1].insert(0,'0.00')
        SO_T[2].insert(0,'AA')
        SO_T[3].insert(0,'Please Delete For Formatting Use Only')
        SO_T[4].insert(0,'00:00:00')
        SO_T[5].insert(0,'0')
        SO_T[6].insert(0,'0')
        SO_T[7].insert(0,'text')
        SO_T[8].insert(0,'Global\Europe\Cardiff\SomeJob\SomeFolder\0000.jpg')
        SO_T[9].insert(0,'SN00000000')
        SO_T[10].insert(0,'SN00000000')
        SO_T[11].insert(0,'Text')
        SO_T[12].insert(0,'Text')
        SO_T[13].insert(0,'0')
        SO_T[14].insert(0,'Text')
        SO_T[15].insert(0,'00:00:00')
        SO_T[16].insert(0,'00/00/0000')
        SO_T[17].insert(0,'00000.mpg')
        SO_T[18].insert(0,'0.00')
        SO_T[19].insert(0,'0.000000000')
        SO_T[20].insert(0,'0.000000000')

        # Add names to columns
        SO_T[0].insert(0,'Ref')
        SO_T[1].insert(0,'Position')
        SO_T[2].insert(0,'OPCode')
        SO_T[3].insert(0,'Text')
        SO_T[4].insert(0,'MPEGPos')
        SO_T[5].insert(0,'Grade')
        SO_T[6].insert(0,'Value')
        SO_T[7].insert(0,'Remark')
        SO_T[8].insert(0,'Photo')
        SO_T[9].insert(0,'StartNode')
        SO_T[10].insert(0,'EndNode')
        SO_T[11].insert(0,'Material')
        SO_T[12].insert(0,'Shape')
        SO_T[13].insert(0,'Diamter')
        SO_T[14].insert(0,'Weather')
        SO_T[15].insert(0,'StartTime')
        SO_T[16].insert(0,'Date')
        SO_T[17].insert(0,'Video')
        SO_T[18].insert(0,'Infiltration')
        SO_T[19].insert(0,'xcoord')
        SO_T[20].insert(0,'ycoord')

        print "Outputting files"

        #open CSV for writing
        outputCSV = '{0}.csv'.format(outputfiles)
        outputLYR = '{0}.lyr'.format(outputfiles)
        outputLYR = outputLYR.replace('/','\\')
        outputSHP = '{0}.shp'.format(outputfiles)
        outputSHP = outputSHP.replace('/','\\')
        outputPRJ = '{0}.prj'.format(outputfiles)
        outputPRJ = outputPRJ.replace('/','\\')
        SO_T = zip(*SO_T)
        with open(outputCSV,'wb') as output:
            writer = csv.writer(output)
            #loop through point list and write to CSV
            for item in SO_T:
                writer.writerow(item)

        # Make shapefile
        out = shapefile.Writer(shapefile.POINT)
        out.autoBalance = 1

        out.field('Ref','C')
        out.field('Position','N',5)
        out.field('OPCode','C')
        out.field('Text','C',200)
        out.field('MPEGPos','C')
        out.field('Grade','N')
        out.field('Value','N')
        out.field('Remark','C',200)
        out.field('Photo','C',200)
        out.field('StartNode','C')
        out.field('EndNode','C')
        out.field('Material','C')
        out.field('Shape','C')
        out.field('Diameter','N')
        out.field('Weather','C')
        out.field('StartTime','C')
        out.field('Date','C')
        out.field('Video','C',200)
        out.field('Infiltration','N',6)
        out.field('xcoord','N')
        out.field('ycoord','N')

        with open(outputCSV, 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            next(reader, None)

            for row in reader:
                Ref = row[0]
                Position = float(row[1])
                OPCode = row[2]
                Text = row[3]
                MPEGPos = row[4]
                Grade = row[5]
                Value = row[6]
                Remark = row[7]
                Photo = row[8]
                StartNode = row[9]
                EndNode = row[10]
                Material = row[11]
                Shape = row[12]
                Diamter = float(row[13])
                Weather = row[14]
                StartTime = row[15]
                Date = row[16]
                Video = row[17]
                Infiltration = float(row[18])
                xcoord = float(row[19])
                ycoord = float(row[20])
                out.point(xcoord,ycoord)
                out.record(Ref,Position,OPCode,Text,MPEGPos,Grade,Value,Remark,Photo,StartNode,EndNode,Material,Shape,Diamter,Weather,StartTime,Date,Video,Infiltration,xcoord,ycoord)

        out.save(outputfiles)
        shutil.copyfile(r"\\global\europe\Cardiff\Jobs\239000\239755-00\4 Internal Project Data\4-40 Calculations\CCTV Automation\27700.prj",outputPRJ)

        # Success GUI
        # Success GUI
        gui = t.Tk()
        def close_window():
            gui.destroy()
        frame = t.Frame(gui)
        frame.pack()
        button = t.Button (frame, text = "Code Run Successfully. Press Button To End", command = close_window)
        button.pack()
        gui.mainloop()
    except Exception as e:
        # Failed GUI
        gui2 = t.Tk()
        def close_window2():
            gui2.destroy()
        frame = t.Frame(gui2)
        frame.pack()
        button = t.Button (frame, text = "Code Failed. Press Button To End", command = close_window2)
        button.pack()
        gui2.mainloop()
        print "FAILED: " + str(e)

# This section builds the user interface
# This is the first row for inputting the csv file location
fld = t.StringVar()
fld1 = t.Message(text ="Location of CCTV files",width=200)
fld2 = t.Entry(window, textvariable=fld,width=80)
fld3 = t.Button(text ="Browse", command = openfld)
fld2.textvariable = fld
# This is the second row for inputting the save as location
osvv = t.StringVar()
osv1 = t.Message(text ="Output Save Location",width=200)
osv2 = t.Entry(window, textvariable=osvv,width=80)
osv3 = t.Button(text ="Browse", command = saveas)
osv2.textvariable = osvv
# This is the third row for setting if infiltration will be run or not
var = t.IntVar()
check = t.Checkbutton(window,text = "Run Infiltration Module",variable=var)
# This creates the run button
run = t.Button(text ="Run", command = main)
# This controls the layout of the user interface
fld1.grid(row=0, column=0, padx=5, pady=5)
fld2.grid(row=0, column=1, padx=5, pady=5)
fld3.grid(row=0, column=2, padx=5, pady=5)
osv1.grid(row=1, column=0, padx=5, pady=5)
osv2.grid(row=1, column=1, padx=5, pady=5)
osv3.grid(row=1, column=2, padx=5, pady=5)
check.grid(row=2, column=1, padx=5, pady=10)
run.grid(row=4, column=1, padx=5, pady=20)
# This opens the user interface
window.mainloop()










