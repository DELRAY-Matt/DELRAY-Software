# coding=utf-8

# Copyright (c) 2018 BigRep GmbH

import re
from typing import List, Tuple
import json
import hashlib

from . import PrintTimeEstimation
from . import proPostProcessing


def get_print_times(first_layer, bigrep_time):
    cura_time = float(re.search(r"TIME:(\d+(\.\d+)?)", first_layer).group(1))
    first_line = ";BigRep Time: {} -- Cura Time: {} -- RelDiff normalized: {} -- RelDiff: {}  -- AbsDiff:{} \n".format(
        bigrep_time, cura_time, 1.0 - bigrep_time/cura_time, bigrep_time/cura_time, bigrep_time-cura_time)
    return first_line


def checkForUnwantedExtruder(data: List[str], extruderTemps: dict) -> Tuple[List[str], float, int]:
    x = re.search(r";?Filament used: (\d*[.]?\d*)m, (\d*[.]?\d*)m", data[0])
    if x:
        T0Material = float(x.group(1))
        T1Material = float(x.group(2))

    if T0Material == 0.0 and T1Material == 0:
        materialDif = 1.0
        nonDominatTool = 1
    elif T0Material >= T1Material:
        materialDif = T1Material * 100.0 / T0Material
        nonDominatTool = 1
    elif T1Material > T0Material:
        materialDif = T0Material * 100.0 / T1Material
        nonDominatTool = 0

    if materialDif <= 1:
        # Remove all unwanted tools in Layer 0 and below
        toolSearch = ".*T{}.*".format(nonDominatTool)
        searchTool = re.compile(toolSearch)
        for index in range(1, min(len(data), 4)):
            data[index] = searchTool.sub(";Dualextrusion not wanted", data[index])

        # Remove heating commands of unwanted tool
        heatSearch = ".*S{}.*".format(extruderTemps["T{}".format(nonDominatTool)])
        searchHeat = re.compile(heatSearch)
        for index in range(2, min(len(data), 4)):
            data[index] = searchHeat.sub(";Dualextrusion not wanted", data[index])

    return data, materialDif, nonDominatTool


def AddSettingsToGCode(machineSettings, extruderSettings, modelInfos) -> str:
    # Save to values in the gcode
    machineData = ";Begin model infos\n"
    for info in modelInfos:
        nameHash = {key: value for (key, value) in info.items() if key in ("name", "hash")}
        machineData += ";Model Info:" + str(json.dumps(nameHash)) + "\n"
        machineData += ";Model Transformation:" + str(json.dumps(info["transformation"])) + "\n"
        machineData += ";Model Bounding Box:" + str(json.dumps(info["bounding_box"])) + "\n"
    machineData += ";End model infos\n\n"
    machineData += ";Begin machine settings\n"
    machineData += ";Machine settings:" + str(json.dumps(machineSettings)) + "\n"
    machineData += ";End machine settings\n"
    machineData += "\n;Begin extruder settings\n"
    machineData += ";Extruder settings:" + str(json.dumps(extruderSettings[0])) + "\n"
    machineData += ";Extruder settings:" + str(json.dumps(extruderSettings[1])) + "\n"
    machineData += ";End extruder settings\n\n"

    return machineData


def integrateTandemMode(data, curaSettings, extruderSettings):
    if curaSettings["br_tandem_enable"]:
        # Change start script
        startScript = data[1].rstrip("\n").split("\n")
        for number, line in enumerate(startScript):
            if line.startswith("T0"):
                realStartPosition = number
            elif line.startswith("M104"):
                heatUpPositon = number
            elif line.startswith("M109"):
                waitHeatUpPositon = number

        startScript.insert(realStartPosition+1, "M802")
        startScript.insert(heatUpPositon+2, "M104 H1 S"+str(extruderSettings[0]["material_temperature"]))
        startScript.insert(waitHeatUpPositon+3, "M109 H1 S"+str(extruderSettings[0]["material_temperature"]))

        data[1] = "\n".join(startScript)

        # Change end script
        data[len(data)-1] = data[len(data)-1] + "M803\n"


def calcTimeEstimation_BigRep(data, curaSettings):
    printTimeEstimationTranslator = {"bigrep_pro": "PRO", "bigrep_onev3": "ONE", "bigrep_pro_1_1": "PRO",
                                     "bigrep_pro_1_2": "PRO", "bigrep_studio": "STUDIO", "bigrep_studio_g2": "STUDIO"}
    if curaSettings["bigrep_time_est"]:
        est_time = PrintTimeEstimation.PrintTimeEstimation(
            printTimeEstimationTranslator[curaSettings["machine_id"]], callback_function=lambda line: None)

        for layer in data:
            lines = layer.rstrip("\n").split("\n")
            for line in lines:
                est_time.process(line)

        est_time.end_print()
        data[0] = get_print_times(data[0], est_time.mechanics.print_time) + data[0]


def nonAsciiHack(data, curaSettings):
    if curaSettings["machine_id"]  not in ("bigrep_pro", "bigrep_pro_1_1", "bigrep_pro_1_2"):
        non_ascii = re.compile(r"[^\x00-\x7F]")
        for layer_number, layer in enumerate(data):
            data[layer_number] = non_ascii.sub("_", layer)


def calcChecksum(data) -> str:
    sha256_hash = hashlib.sha256()
    for layer in data:
        sha256_hash.update(layer.encode("utf-8"))

    return sha256_hash.hexdigest()

def addPROParameterSettings(curaSettings: dict) -> str:
    additionalLines = []
    for number, extruder in enumerate(curaSettings["pro_ex_settings"]):
        # Check Values
        additionalLines.append("\n; Index[{}] Check EXT Pos: {}]\n".format((number), str(extruder["check_ex_pos"])))
        additionalLines.append("; Index[{}] Check Variant: {}]\n".format((number), extruder["check_variant"]))

        # Feeder Curves
        additionalLines.append("\nSSD[SD.stFeederParam.arK0[{}]={}]\n".format((extruder["check_ex_pos"] + 1), extruder["br_feeder_k0"]))
        additionalLines.append("SSD[SD.stFeederParam.arK1[{}]={}]\n".format((extruder["check_ex_pos"] + 1), extruder["br_feeder_k1"]))
        additionalLines.append("SSD[SD.stFeederParam.arK2[{}]={}]\n".format((extruder["check_ex_pos"] + 1), extruder["br_feeder_k2"]))

        # Pump Curves
        additionalLines.append("\nSSD[SD.stPumpParam.arK0[{}]={}]\n".format((extruder["check_ex_pos"] + 1), extruder["br_pump_k0"]))
        additionalLines.append("SSD[SD.stPumpParam.arK1[{}]={}]\n".format((extruder["check_ex_pos"] + 1), extruder["br_pump_k1"]))
        additionalLines.append("SSD[SD.stPumpParam.arK2[{}]={}]\n".format((extruder["check_ex_pos"] + 1), extruder["br_pump_k2"]))
        # Pump Standby
        additionalLines.append("SSD[SD.stPumpParam.arSTB[{}]={}]\n".format((extruder["check_ex_pos"] + 1), extruder["br_pump_stb"]))

        # Timings aka Fast Action
        additionalLines.append("\nSSD[SD.stTimings.ausiPump[{}]={}]\n".format((extruder["check_ex_pos"] + 1), extruder["br_timings_pump"]))
        additionalLines.append("SSD[SD.stTimings.ausiXYZ[{}]={}]\n".format((extruder["check_ex_pos"] + 1), extruder["br_timings_xyz"]))
        additionalLines.append("SSD[SD.stTimings.ausiFeeder[{}]={}]\n".format((extruder["check_ex_pos"] + 1), extruder["br_timings_feeder"]))           

    additionalString = "".join(additionalLines)
    additionalString = additionalString + "\n"
    
    return additionalString

# Sample of input variables.
# machineSettings
# {'bed_temperature': 80, 'machine': 'bigrep_pro'}
# extruderSettings
# [{'active': False, 'material_temperature': 235, 'extruder': 'EX1', 'material': {'brand': 'BigRep', 'color_code': '#303030', 'GUID': '6fc81be4-a780-49a9-8f19-c8f4f8b96ab0', 'type': 'PA6/66'}, 'position': 'T0', 'variant': 'MXT 1 mm'}, {'active': False, 'material_temperature': 235, 'extruder': 'EX2', 'material': {'brand': 'BigRep', 'color_code': '#303030', 'GUID': '6fc81be4-a780-49a9-8f19-c8f4f8b96ab0', 'type': 'PA6/66'}, 'position': 'T1', 'variant': 'MXT 1 mm'}]
# featureTimes
# ;FeatureTime: Skin: 2366
# ;FeatureTime: Support Interface: 0
# ;FeatureTime: Support: 0
# ;FeatureTime: Skirt: 103
# ;FeatureTime: Retractions: 309
# ;FeatureTime: Other: 0
# ;FeatureTime: Infill: 5710
# ;FeatureTime: Outer Wall: 6265
# ;FeatureTime: Travel: 146
# ;FeatureTime: Support Infill: 0
# ;FeatureTime: Inner Walls: 1922
# curaSettings["br_change_extruder_enable"] = False
# curaSettings["extruders_enabled_count"] = 1
# curaSettings["machine_id"] = "bigrep_pro"
# curaSettings["bigrep_time_est"] = True/False
# curaSettings["br_tandem_enable"] = True/False

# curaSettings["br_mxt_feeder_k0"] = 0
# curaSettings["br_mxt_feeder_k1"] = 1.0065
# curaSettings["br_mxt_feeder_k2"] = 0.0013

# curaSettings["extruder_temps"] = self.getExtruderTemps(curaSettings)

def execute(data, curaSettings, machineSettings, extruderSettings, featureTimes, mode, version, modelInfos): # pylint: disable=too-many-arguments

    versions = version.split("-")
    versionLine = ";BigRep Blade Version " + versions[0] + "\n;Rev: " + versions[1] + "\n"

    searchFan = re.compile(r"M106.*")
    data[2] = searchFan.sub("M107", data[2])  # Replace all M106 in Layer 0.

    if curaSettings["br_change_extruder_enable"]:
        extruderSelect = re.compile(r"T0.*")
        for layer_number, layer in enumerate(data):
            data[layer_number] = extruderSelect.sub("T1", layer)

    if curaSettings["extruders_enabled_count"] == 1:
        data, materialDif, nonDominatTool = checkForUnwantedExtruder(data, curaSettings["extruder_temps"])
        if materialDif <= 1:
            extruderSettings[nonDominatTool]["material_used"] = 0

    calcTimeEstimation_BigRep(data, curaSettings)

    if curaSettings["machine_id"] in ("bigrep_pro", "bigrep_pro_1_1", "bigrep_pro_1_2"):
        data = proPostProcessing.main(data, mode, extruderSettings)

    data[0] = versionLine + str(data[0])

    data[1] = featureTimes + data[1]

    # Add settings into the gcode
    machineData = AddSettingsToGCode(machineSettings, extruderSettings, modelInfos)
    data[0] = data[0] + "\n" + machineData

    integrateTandemMode(data, curaSettings, extruderSettings)  # Get Tandem Mode into gcode

    # Get PRO Extruder Parameter Settings into gcode
    if curaSettings["machine_id"] in ("bigrep_pro", "bigrep_pro_1_1", "bigrep_pro_1_2"):
        PROExSettings = addPROParameterSettings(curaSettings)
        data[1] = str(PROExSettings) + data[1]

    nonAsciiHack(data, curaSettings)  # Hack out non ascii chars

    data[-1] = data[-1] + "\n;Checksum: " + str(calcChecksum(data)) + "\n"  # Adding checksum

    return data
