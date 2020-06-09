# Copyright (c) 2019 BigRep
# The Batch Printing plugin is released under the terms of the LGPLv3.

import math
from typing import Any, Tuple
import copy
import numpy

from UM.Extension import Extension
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Math.Quaternion import Quaternion
from UM.Math.Vector import Vector
from UM.Scene.SceneNode import SceneNode
from UM.Message import Message
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.i18n import i18nCatalog

from cura.Settings.ExtruderManager import ExtruderManager
from cura.CuraApplication import CuraApplication

from .BatchIterator import BatchIterator
from .BatchArrangement import BatchArrangement

i18n_catalog = i18nCatalog("BatchPrintingPlugin")


class BatchPrintingPlugin(Extension):
    def __init__(self):
        super().__init__()
        self.addMenuItem(i18n_catalog.i18n("Arrange objects for mixed mode"), self.arrangeObjectsForMixedMode)
        self.addMenuItem(i18n_catalog.i18n("Populate build plate completely"), self.populateBuildPlateCompletely)
        self.addMenuItem(i18n_catalog.i18n("Populate build plate for sequential printing"), self.populateBuildPlateSequential)
        self._message = None
        self._scene = CuraApplication.getInstance().getController().getScene()  # type: Scene

    @staticmethod
    def _extractBox(node):
        boundingBox = node.getBoundingBox()
        return (boundingBox.minimum.getData(), boundingBox.maximum.getData())

    @staticmethod
    def _securityDists(global_stack):
        polygon = numpy.array(global_stack.getProperty("machine_head_with_fans_polygon", "value"))

        minPt = polygon[0]
        maxPt = polygon[0]
        for point in polygon[1:]:
            minPt = numpy.minimum(minPt, point)
            maxPt = numpy.maximum(maxPt, point)

        maxPt -= minPt

        return (maxPt[0], maxPt[1])

    ##   Private convenience function to get a setting from the correct extruder (as defined by limit_to_extruder property).
    @staticmethod
    def _getSettingProperty(global_stack, node, setting_key: str, prop: str = "value") -> Any:
        if global_stack is None or node is None:
            return None
        per_mesh_stack = node.callDecoration("getStack")
        if per_mesh_stack:
            return per_mesh_stack.getProperty(setting_key, prop)

        extruder_index = global_stack.getProperty(setting_key, "limit_to_extruder")
        if extruder_index == "-1":
            # No limit_to_extruder
            extruder_stack_id = node.callDecoration("getActiveExtruder")
            if not extruder_stack_id:
                # Decoration doesn't exist
                extruder_stack_id = ExtruderManager.getInstance().extruderIds["0"]
            extruder_stack = ContainerRegistry.getInstance().findContainerStacks(id=extruder_stack_id)[0]
            return extruder_stack.getProperty(setting_key, prop)
        else:
            # Limit_to_extruder is set. The global stack handles this then
            return global_stack.getProperty(setting_key, prop)


    @staticmethod
    def _adhesionTypeAndMargin(global_stack, node) -> Tuple[str, float]:
        extra_margin = 0

        # Compensate for raft/skirt/brim
        # Add extra margin depending on adhesion type
        adhesion_type = global_stack.getProperty("adhesion_type", "value")

        if adhesion_type == "raft":
            extra_margin = max(0, BatchPrintingPlugin._getSettingProperty(global_stack, node, "raft_margin"))
        elif adhesion_type == "brim":
            extra_margin = max(0, BatchPrintingPlugin._getSettingProperty(global_stack, node, "brim_line_count") * BatchPrintingPlugin._getSettingProperty(global_stack, node, "skirt_brim_line_width"))
        elif adhesion_type == "none":
            extra_margin = 0
        elif adhesion_type == "skirt":
            extra_margin = max(
                0, BatchPrintingPlugin._getSettingProperty(global_stack, node, "skirt_gap") +
                BatchPrintingPlugin._getSettingProperty(global_stack, node, "skirt_line_count") * BatchPrintingPlugin._getSettingProperty(global_stack, node, "skirt_brim_line_width"))

        return (adhesion_type, extra_margin)


    @staticmethod
    def _getMachineDescr(node):
        machineID = CuraApplication.getInstance().getMachineManager().activeMachine.definition.getId()
        isStudio = machineID in ("bigrep_studio", "bigrep_studio_g2")

        global_stack = CuraApplication.getInstance().getGlobalContainerStack()

        secDists = BatchPrintingPlugin._securityDists(global_stack)
        securityDistance0 = secDists[0] if isStudio else secDists[1]
        securityDistance1 = secDists[1] if isStudio else secDists[0]

        adhesionType, adhesionMargin = BatchPrintingPlugin._adhesionTypeAndMargin(global_stack, node)

        machineDescr = {
            "machineID": machineID,
            "isStudio": isStudio,
            "machine_size": [global_stack.getProperty("machine_width", "value"), global_stack.getProperty("machine_depth", "value")],
            "machine_preferedStartPoint": [global_stack.getProperty("machine_width_prefered_start_point", "value"), global_stack.getProperty("machine_depth_prefered_start_point", "value")],
            "adhesionType": adhesionType,
            "adhesionMargin": adhesionMargin,
            "tandemMode": global_stack.getProperty("br_tandem_enable", "value"),
            "batch_printing_90deg_rotation": global_stack.getProperty("batch_printing_90deg_rotation", "value"),
            "securityDistance0": securityDistance0,
            "securityDistance1": securityDistance1
        }

        return machineDescr

    @staticmethod
    def rotate90(node):
        rotation = Quaternion.fromAngleAxis(-0.5 * math.pi, Vector(0, 1, 0))
        node.rotate(rotation, SceneNode.TransformSpace.World)

    @staticmethod
    def _optimizeOrientation(node):
        bbox = BatchPrintingPlugin._extractBox(node)
        diag_x = bbox[1][0] - bbox[0][0]
        diag_y = bbox[1][2] - bbox[0][2]
        if diag_y > diag_x:
            BatchPrintingPlugin.rotate90(node)


    @staticmethod
    def run(nodes) -> bool:        
        bbox_list = [BatchPrintingPlugin._extractBox(node) for node in nodes]

        translations, warning = BatchArrangement(BatchPrintingPlugin._getMachineDescr(nodes[0])).process(bbox_list)

        for counter, node in enumerate(nodes):
            vec = Vector(translations[counter][0], translations[counter][1], translations[counter][2])
            node.translate(vec, SceneNode.TransformSpace.World)

        return warning


    def arrangeObjectsForMixedMode(self, optimize=True):
        # If we still had a message open from last time, hide it.
        if self._message:
            self._message.hide()

        selected_nodes = self._collectNodes()
        if not selected_nodes:
            self._message = Message(i18n_catalog.i18nc("@info:status", "No objects to arrange."),
                                    title=i18n_catalog.i18nc("@info:title", "Batch Printing"))
            self._message.show()
            return

        if optimize:
            global_stack = CuraApplication.getInstance().getGlobalContainerStack()
            optimize = global_stack.getProperty("batch_printing_90deg_rotation", "value")
 
        if optimize:
            for node in selected_nodes:
                BatchPrintingPlugin._optimizeOrientation(node)

        warning = BatchPrintingPlugin.run(selected_nodes)

        if warning:
            self._message = Message(i18n_catalog.i18nc(
                "@info:status", "Unable to find a location within the build volume for all objects."), title=i18n_catalog.i18nc("@info:title", "Batch Printing"))
            self._message.show()

    def _collectNodes(self):
        return [node for node in BatchIterator(self._scene.getRoot())]  # pylint: disable=unnecessary-comprehension


    def populateBuildPlateCompletely(self):
        self.populateBuildPlate(True)


    def populateBuildPlateSequential(self):
        self.populateBuildPlate(False)

    def populateBuildPlate(self, complete: bool):
        # If we still had a message open from last time, hide it.
        if self._message:
            self._message.hide()

        nodes = self._collectNodes()

        if not nodes:
            self._message = Message(i18n_catalog.i18nc("@info:status", "No objects to arrange."),
                                    title=i18n_catalog.i18nc("@info:title", "Batch Printing"))
            self._message.show()
            return
        elif len(nodes) > 1:
            self._message = Message(i18n_catalog.i18nc("@info:status", "This feature does just work for a single object."),
                                    title=i18n_catalog.i18nc("@info:title", "Batch Printing"))
            self._message.show()
            return

        # If object is part of a group, multiply group
        current_node = nodes[0]
        while current_node.getParent() and (current_node.getParent().callDecoration("isGroup") or current_node.getParent().callDecoration("isSliceable")):
            current_node = current_node.getParent()


        batchArrangement = BatchArrangement(BatchPrintingPlugin._getMachineDescr(current_node))
        if batchArrangement.shallRotateForPopulate(BatchPrintingPlugin._extractBox(current_node)):
            BatchPrintingPlugin.rotate90(current_node)

        if complete:
            multiplier = batchArrangement.calcMultiplier(BatchPrintingPlugin._extractBox(current_node))
        else:
            multiplier = batchArrangement.calcMultiplierSequential(BatchPrintingPlugin._extractBox(current_node))

        new_nodes = [copy.deepcopy(current_node) for _ in range(multiplier - 1)]  # We already one item!

        if new_nodes:
            # Same build plate
            for new_node in new_nodes:
                build_plate_number = current_node.callDecoration("getBuildPlateNumber")
                new_node.callDecoration("setBuildPlateNumber", build_plate_number)
                for child in new_node.getChildren():
                    child.callDecoration("setBuildPlateNumber", build_plate_number)

            op = GroupedOperation()
            for new_node in new_nodes:
                op.addOperation(AddSceneNodeOperation(new_node, current_node.getParent()))
            op.push()

        self.arrangeObjectsForMixedMode(optimize=False)

        self._message = Message(i18n_catalog.i18nc("@info:status", "Build plate is populated with " + str(multiplier) + " objects."),
                                title=i18n_catalog.i18nc("@info:title", "Batch Printing"))
        self._message.show()
