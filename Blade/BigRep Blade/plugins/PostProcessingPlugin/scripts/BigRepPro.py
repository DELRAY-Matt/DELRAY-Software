# coding=utf-8

# Copyright (c) 2018 BigRep GmbH

from typing import cast
import os

from UM.Application import Application
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator

import cura.CuraApplication # To get the global container stack to find the current machine.
from cura.CuraApplication import CuraApplication
from cura.Snapshot import Snapshot

import plugins.PostProcessingPlugin.BigRep_PostProcessing.BigRepPostProcessing as BigRepPostProcessing

from ..Script import Script # pylint: disable=relative-beyond-top-level

class BigRepPro(Script):
    def getSettingDataString(self): # pylint: disable=no-self-use
        return """{
            "name":"BigRep Pro",
            "key": "BigRepPro",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "bigrep_time_est":
                {
                    "label": "Use BigRep time estimation.",
                    "description": "This is accurate and slow. You won't need it usually!",
                    "type": "bool",
                    "default_value": false
                }
            }
        }"""


    @staticmethod
    def extractModelInfos():
        infos = []
        for node in DepthFirstIterator(Application.getInstance().getController().getScene().getRoot()):
            if node.callDecoration("isSliceable"):
                model = dict()
                model["hash"] = node.getMeshData().getHash()

                bounding_box = node.getBoundingBox()
                model["bounding_box"] = {"minimum": {"x": bounding_box.minimum.x,
                                                     "y": bounding_box.minimum.y,
                                                     "z": bounding_box.minimum.z},
                                         "maximum": {"x": bounding_box.maximum.x,
                                                     "y": bounding_box.maximum.y,
                                                     "z": bounding_box.maximum.z}}
                model["transformation"] = [[node.getWorldTransformation().at(0, 0), node.getWorldTransformation().at(0, 1), node.getWorldTransformation().at(0, 2), node.getWorldTransformation().at(0, 3)],
                                           [node.getWorldTransformation().at(1, 0), node.getWorldTransformation().at(1, 1), node.getWorldTransformation().at(1, 2), node.getWorldTransformation().at(1, 3)],
                                           [node.getWorldTransformation().at(2, 0), node.getWorldTransformation().at(2, 1), node.getWorldTransformation().at(2, 2), node.getWorldTransformation().at(2, 3)],
                                           [node.getWorldTransformation().at(3, 0), node.getWorldTransformation().at(3, 1), node.getWorldTransformation().at(3, 2), node.getWorldTransformation().at(3, 3)]]
                model["name"] = node.getName()

                infos.append(model)
        
        return infos


    @staticmethod
    def get_extruders_and_material_usage(global_stack):
        extruders = list(global_stack.extruders.values())

        lenghts = Application.getInstance().getPrintInformation().materialLengths
        weights = Application.getInstance().getPrintInformation().materialWeights
        costs = Application.getInstance().getPrintInformation().materialCosts

        extruders_more = list(zip(extruders, lenghts, weights, costs))
        extruders_more.sort(key=lambda extruder_more: extruder_more[0].getMetaDataEntry("position"))
        extruders = [extruders_more_val[0] for extruders_more_val in extruders_more]
        lenghts = [extruders_more_val[1] for extruders_more_val in extruders_more]
        weights = [int(extruders_more_val[2]) for extruders_more_val in extruders_more]
        costs = [extruders_more_val[3] for extruders_more_val in extruders_more]

        return extruders, lenghts, weights, costs


    @staticmethod
    def get_machine_settings():

        application = cast(CuraApplication, Application.getInstance())
        machine_manager = application.getMachineManager()
        global_stack = machine_manager.activeMachine

        extruders, lenghts, weights, costs = BigRepPro.get_extruders_and_material_usage(global_stack)

        extruderData = []

        for number, extruder in enumerate(extruders):
            extruder_dict = {}
            extruder_dict["position"] = "T" + extruder.getMetaDataEntry("position", "0")
            if Application.getInstance().getGlobalContainerStack().getProperty("br_change_extruder_enable", "value") and number == 0:
                extruder_dict["position"] = "T1"

            extruder_dict["variant"] = extruder.variant.getName()
            extruder_dict["material"] = {}
            extruder_dict["material"]["type"] = extruder.material.getMetaData().get("material", "")
            extruder_dict["material"]["color_code"] = extruder.material.getMetaData().get("color_code", "")
            extruder_dict["material"]["brand"] = extruder.material.getMetaData().get("brand", "")
            extruder_dict["material"]["GUID"] = extruder.material.getMetaData().get("GUID", "")
            extruder_dict["material_temperature"] = extruder.getProperty("material_print_temperature", "value")
            extruder_dict["material_length"] = lenghts[number]
            extruder_dict["material_weight"] = weights[number]
            extruder_dict["material_cost"] = costs[number]
            extruder_dict["material_diameter"] = extruder.getProperty("material_diameter", "value") 
            extruder_dict["material_density"] = extruder.getMetaDataEntry("properties", {}).get("density", 0)
            extruder_dict["active"] = (float(extruder_dict["material_length"]) != 0)

            if Application.getInstance().getGlobalContainerStack().getProperty("br_change_extruder_enable", "value") and number == 1:
                for key in extruder_dict:
                    extruder_dict[key] = None
                    if key == "position":
                        extruder_dict[key] = "T0"

            extruderData.append(extruder_dict)
        
        machineData = {}
        machineData["machine"] = global_stack.definition.getId()
        machineData["bed_temperature"] = extruders[1].getProperty("material_bed_temperature", "value")

        return machineData, extruderData

    @staticmethod
    def getExtruderTemps(curaSettings):
        extruderTemps = dict()

        if curaSettings["extruders_enabled_count"] == 1:
            application = cast(CuraApplication, Application.getInstance())
            machine_manager = application.getMachineManager()
            global_stack = machine_manager.activeMachine

            extruders = list(global_stack.extruders.values())
            extruders = sorted(extruders, key=lambda extruder: extruder.getMetaDataEntry("position"))

            for number, extruder in enumerate(extruders):
                extruderTemps["T{}".format(number)] = extruder.getProperty("material_print_temperature", "value")

        return extruderTemps

    @staticmethod
    def getPROExtruderSettings():
        application = cast(CuraApplication, Application.getInstance())
        machine_manager = application.getMachineManager()
        global_stack = machine_manager.activeMachine
        extruders = list(global_stack.extruders.values())

        extruderPROSettings = []

        for extruder in extruders:
            settingsPair = {}
            settingsPair["check_ex_pos"] = int(extruder.getMetaDataEntry("position", "0"))
            settingsPair["check_variant"] = extruder.variant.getName()
            settingsPair["br_feeder_k0"] = extruder.getProperty("br_feeder_k0", "value")
            settingsPair["br_feeder_k1"] = extruder.getProperty("br_feeder_k1", "value")
            settingsPair["br_feeder_k2"] = extruder.getProperty("br_feeder_k2", "value")
            settingsPair["br_pump_k0"] = extruder.getProperty("br_pump_k0", "value")
            settingsPair["br_pump_k1"] = extruder.getProperty("br_pump_k1", "value")
            settingsPair["br_pump_k2"] = extruder.getProperty("br_pump_k2", "value")
            settingsPair["br_pump_stb"] = extruder.getProperty("br_pump_stb", "value")
            settingsPair["br_timings_pump"] = extruder.getProperty("br_timings_pump", "value")
            settingsPair["br_timings_xyz"] = extruder.getProperty("br_timings_xyz", "value")
            settingsPair["br_timings_feeder"] = extruder.getProperty("br_timings_feeder", "value")

            extruderPROSettings.append(settingsPair)

        return extruderPROSettings


    def getCuraSettings(self):
        curaSettings = {}
        curaSettings["br_change_extruder_enable"] = Application.getInstance().getGlobalContainerStack().getProperty("br_change_extruder_enable", "value")
        curaSettings["extruders_enabled_count"] = Application.getInstance().getGlobalContainerStack().getProperty("extruders_enabled_count", "value")
        curaSettings["machine_id"] = cura.CuraApplication.CuraApplication.getInstance().getMachineManager().activeMachine.definition.getId()
        curaSettings["machine_name"] = cura.CuraApplication.CuraApplication.getInstance().getMachineManager().activeMachineId
        curaSettings["bigrep_time_est"] = self.getSettingValueByKey("bigrep_time_est")
        curaSettings["br_tandem_enable"] = Application.getInstance().getGlobalContainerStack().getProperty("br_tandem_enable", "value")

        curaSettings["pro_ex_settings"] = BigRepPro.getPROExtruderSettings()

        curaSettings["infill_density"] = Application.getInstance().getGlobalContainerStack().getProperty("infill_sparse_density", "value")
        curaSettings["layer_height"] = Application.getInstance().getGlobalContainerStack().getProperty("layer_height", "value")

        curaSettings["extruder_temps"] = BigRepPro.getExtruderTemps(curaSettings)

        return curaSettings


    @staticmethod
    def get_feature_times(cura_featureTimes):
        def get_total_seconds(duration):
            return duration.days * 3600 * 24 + duration.hours * 3600 + duration.minutes * 60 + duration.seconds

        feature_times = ""   
        for feature, duration in cura_featureTimes.items():
            feature_times = feature_times + ";FeatureTime: {}: {}\n".format(feature, get_total_seconds(duration))

        return feature_times


    @staticmethod
    def getPrintHours() -> int:
        timeDuration = Application.getInstance().getPrintInformation().currentPrintTime
        printTime = timeDuration.days * 24 + timeDuration.hours
        if Application.getInstance().getPrintInformation().currentPrintTime.minutes > 20:
            printTime += 1
        return printTime


    @staticmethod
    def preparePrintReport(outputDirectory: str, filename: str):
        if not os.path.exists(outputDirectory):
            os.mkdir(outputDirectory)

        # must be called from the main thread because of OpenGL        
        snapshot = Snapshot.snapshot(width=600, height=600)        
        snapshot.save(outputDirectory + "\\" + filename) 

    def execute(self, data):
        curaSettings = self.getCuraSettings()
        machineSettings, extruderSettings = BigRepPro.get_machine_settings()
        featureTimes = BigRepPro.get_feature_times(Application.getInstance().getPrintInformation().getFeaturePrintTimes())

        version_info = Application.getInstance().getVersion() 
        # version_info = Application.getInstance().getVersion() + ":" + Application.getInstance().getBuildType() # build type is currently not available!

        modelInfos = BigRepPro.extractModelInfos()

        # BigRep Sales Report: Please comment in to activate it.
        # outputDirectory = r"C:\print_report"
        # import plugins.PostProcessingPlugin.BigRep_PostProcessing.Report as Report
        # self.preparePrintReport(outputDirectory, modelInfos[0]["name"].split('.')[0] + ".png")
        # Report.generatePrintReport(outputDirectory, modelInfos[0]["name"].split('.')[0], curaSettings, extruderSettings, BigRepPostProcessing.getPrintHours())

        return BigRepPostProcessing.execute(data, curaSettings, machineSettings, extruderSettings, featureTimes, mode="cura", version=version_info, modelInfos=modelInfos)
