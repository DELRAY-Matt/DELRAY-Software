# coding=utf-8

# Copyright (c) 2018 BigRep GmbH
# This file is part of Blade.
# Blade can not be copied and/or distributed without the express permission of BigRep.

import re
from typing import List, Tuple
import json
import math

header = """
;Minimal Firmware Version: 1.5.1

;Begin start script
M601 ;Arm InterLocks
M361 ;start filtration system
M324 ;start chamber blowers
M351 ;Start print job
JKC(1) ;activate jerk control
JKC(KLL3,TIME30) ;set jerk control parameters

G592(TOL0.1)
;End start script
"""

firstLayerIntro = """
WAIT
10 IF APOS(3) >= 870 THEN
N20 G1 Z800 F400
N30 WAIT
30 ENDIF
"""


footer = """
;Begin end script
;Go to park position
WAIT
100 IF APOS(3) >= 880 THEN
N110 G1 Z950 F400
N120 G1 X900 Y850 F1800
120 ELSE 
N130 G1 Z[APOS(3)+50] F400
N140 G1 X900 Y900 F1800
130 ENDIF
WAIT

M210 ;turn off T0
M220 ;turn off T1
M200 ;turn off bed
;this totally bosch stuff
M400 ;Lift Extruder T0
M410 ;Lift Extruder T1
M600 ;Disarm InterLocks
M350 ;End Of PrintJob
M30 ;End Of Program
;End end script
"""

# global variables
regexTypeSearch = re.compile(r";?TYPE:(.*)")
currentTool = -1
currentFeatureType = str()
SplineTolerance = 0.1
layerEValue = {"T0": 0.0, "T1": 0.0}
modus = str()

extruderSettings = [{'material_diameter': 2.85, 'material_density': 1.12}, {'material_diameter': 2.85, 'material_density': 1.12}]  # PA6.66


def calcWeights(layerEValue):
    weights = {}
    for number, key in enumerate(layerEValue.keys()):
        length = layerEValue[key]  # mm
        amount = length * math.pi * float(extruderSettings[number]["material_diameter"])**2 / 4.0  # mm³
        density = float(extruderSettings[number]["material_density"]) / 1000  # g/cm³ -> g/mm³
        weight = amount * density  # result: g
        weights[key] = round(weight, 3)

    return ";Filament weight for next layer: " + str(json.dumps(weights, sort_keys=True))


def processLine(line):
    if line.startswith("G1"):
        yield G1(line)
    else:
        if line.startswith("G0"):
            yield G0(line)
        else:
            if not line:  # Avoid index errors when line is empty
                yield line
            else:
                if line.startswith(";"):
                    yield processComment(line)
                else:
                    if ";" not in line:
                        command = line.split()[0]
                    else:
                        command = line.split(";")[0].split()[0]

                    if validCodes.get(command) is not None:
                        yield validCodes[command](line)
                    else:
                        yield ";" + line


def processComment(line: str) -> str:
    global currentFeatureType
    featureTypeSearch = regexTypeSearch.search(line)
    if featureTypeSearch:
        currentFeatureType = featureTypeSearch.group(1).lower()

    return line


def M104(line: str) -> str:
    # Set Extruder Temperature
    splitLine = line.split()
    if len(splitLine) == 2:
        sValue = line.split()[1][1:]
        return "M2{}1 S1={}".format(currentTool + 1, sValue)
    else:
        sValue = line.split()[2][1:]
        tValue = int(line.split()[1][1:])
        return "M2{}1 S1={}".format(tValue + 1, sValue)


def M109(line: str) -> str:
    # Set Extruder Temperature and wait
    splitLine = line.split()
    if len(splitLine) == 2:
        sValue = line.split()[1][1:]
        return "M2{}2 S1={}".format(currentTool + 1, sValue)
    else:
        sValue = line.split()[2][1:]
        tValue = int(line.split()[1][1:])
        return "M2{}2 S1={}".format(tValue + 1, sValue)


def M140(line: str) -> str:
    # Bed Heating
    sValue = line.split()[1][1:]
    if sValue == "0":
        return "M200"
    else:
        return "M201 S1={}".format(sValue)


def M190(line: str) -> str:
    # Bed Heating and wait
    sValue = line.split()[1][1:]
    if sValue == "0":
        return "M200"
    else:
        return "M202 S1={}".format(sValue)


def M106(line: str) -> str:
    # Set fan speed
    fanValue = round(float(line.split("S")[1])/2.55, 1)
    return "M3{}1 S1={}".format(currentTool + 1, fanValue)


def M107(line: str) -> str: # pylint: disable=unused-argument
    # Disable fan
    return "M3{}0".format(currentTool + 1)


def toolChange(line: str) -> str:
    global currentTool

    if line == "T0":
        if currentTool == 0:
            return ";" + line + "Tool already selected"
        else:
            currentTool = 0
            return "SELTZERO"

    elif line == "T1":
        if currentTool == 1:
            return ";" + line + " - Tool already selected"
        else:
            currentTool = 1
            return "SELTONE"

    # This should never happen
    return ";" + line


def G0(line: str) -> str:
    return line.replace("G0", "G1")


def G1(line: str) -> str:
    global layerEValue
    splitedline = line.split()

    for tag in splitedline:
        if tag.startswith("E"):
            eValue = float(tag[1:])
            layerEValue["T"+str(currentTool)] += eValue
            newline = line.split("E")[0]
            newline += "EX=IC({:.5f}*@EX{}_FACTOR)".format(eValue, currentTool + 1)
            return newline

    return line


def processSingleLayer(numberLayer: Tuple[int, str]) -> str:
    global layerEValue

    number, layer = numberLayer
    newLines = []  # type: ignore
    lines = layer.rstrip("\n").split("\n")
    for line in lines:
        tempNewLines = processLine(line)
        newLines += tempNewLines

    for tool, eValue in layerEValue.items():
        layerEValue[tool] = round(eValue, 3)
    if modus == "cura":
        insertLayerNumber = calcWeights(layerEValue)
        newLines.insert(1, insertLayerNumber)
    else:
        insertLayerNumber = ";LAYER:" + str(number - 1) + "\n" + calcWeights(layerEValue)
        newLines.insert(0, insertLayerNumber)

    newLines.insert(2, "G74(HOME) EX 0\n")
    if number == 2:
        newLines.insert(4, firstLayerIntro)


    layerEValue["T0"] = 0.0
    layerEValue["T1"] = 0.0

    newLayer = "\n".join(newLines)
    newLayer += "\n"

    return newLayer


def processMultiLayers(layers: List[str]) -> List[str]:
    newLayers = list()
    for number, layer in enumerate(layers):
        newLayers.append(processSingleLayer((number, layer)))

    newLayers[0] = header + newLayers[0]
    newLayers[(len(newLayers) - 1)] = newLayers[(len(newLayers) - 1)] + footer

    return newLayers


# Setup G/M-Code interpretation
validCodes = {
    "T0": toolChange,
    "T1": toolChange,

    "G0": G0,  # Travel moves
    "G1": G1,  # Extrusion moves
    "G20": None,
    "G21": None,
    "G28": None,
    "G90": None,
    "G91": None,
    "G92": None,

    "M0": None,
    "M82": None,
    "M83": None,
    "M84": None,
    "M104": M104,  # Set extruder temp
    "M105": None,
    "M106": M106,  # Set fan speed
    "M107": M107,  # Disable fan speed
    "M109": M109,  # Set extruder temp and wait
    "M110": None,
    "M114": None,
    "M140": M140,  # Set bed temp
    "M190": M190,  # Set bed temp and wait
    "M220": None,
    "M221": None,
    "M600": None,
    "M601": None,
    "M602": None,
    "M603": None,
    "M604": None
}


def main(data, mode: str, extruderSettings_new: List[dict] = None):
    global modus
    global currentTool
    modus = mode
    currentTool = -1

    if extruderSettings_new:
        global extruderSettings
        extruderSettings = extruderSettings_new

    if modus == "cura":
        # input is original cura
        return processMultiLayers(data)

    if modus == "bench":
        # input is gcode as cura faked list with strings
        return processMultiLayers(data)

    if modus == "test":
        # input is gcode as file
        with open(data) as file:
            gcode = file.read()
        layers = re.split(r";LAYER:\d+", gcode)
        newLayers = processMultiLayers(layers)
        newGCode = "".join(newLayers)  # type: ignore

        return newGCode

    return data
