# Copyright (c) 2019 BigRep
# The Batch Printing plugin is released under the terms of the LGPLv3.

import collections
from copy import deepcopy
from typing import List, Tuple

import numpy  # type: ignore


SlotY_item = collections.namedtuple('SlotY_item', 'endY itemsX')
ItemX_item = collections.namedtuple('ItemX_item', 'endX bboxCounter')
Machine_Size = collections.namedtuple('Macnine_Size', 'max_x max_y')
Security_Distance = collections.namedtuple('Security_Distance', 'distance layerByLayer object')


class BatchArrangement:

    def __init__(self, machineDescr: dict):
        # self.machineID = machineDescr["machineID"]
        self.isStudio = machineDescr["isStudio"]

        adhesionMargin = machineDescr["adhesionMargin"]
        adhesionType = machineDescr["adhesionType"]

        self.preferedStartPoint = machineDescr["machine_preferedStartPoint"]

        self.tandemMode = machineDescr["tandemMode"]

        max_x = machineDescr["machine_size"][0] if not self.tandemMode else machineDescr["machine_size"][0]/2.0
        self.machineSize = Machine_Size(max_x=max_x, max_y=machineDescr["machine_size"][1])

        securityDistance = machineDescr["securityDistance0"]
        securityDistance_Object = machineDescr["securityDistance1"]

        securityDistanceLayerByLayer = securityDistance_Object + 2 * adhesionMargin
        if adhesionType != "raft":
            # Not rafts are just one layer high and can be "ignored" for the security distance.
            securityDistance = max(0.0, securityDistance - adhesionMargin)

        self.securityDistance = Security_Distance(distance=securityDistance, layerByLayer=securityDistanceLayerByLayer, object=securityDistance_Object)        

        self.optimize90deg = machineDescr["batch_printing_90deg_rotation"]

    def shallRotateForPopulate(self, box: Tuple[numpy.ndarray, numpy.ndarray]) -> bool:

        def _switchXYBox(box):
            newBox = deepcopy(box)
            newBox[0][0], newBox[0][2] = newBox[0][2], newBox[0][0]
            newBox[1][0], newBox[1][2] = newBox[1][2], newBox[1][0]
            return newBox

        if not self.optimize90deg:
            return False

        switchBox = _switchXYBox(box)

        multiplier = self.calcMultiplier(box)
        multiplierSequential = self.calcMultiplierSequential(box)

        switch_multiplier = self.calcMultiplier(switchBox)
        switch_multiplierSequential = self.calcMultiplierSequential(switchBox)

        if multiplierSequential < switch_multiplierSequential:
            return True
        elif multiplierSequential > switch_multiplierSequential:
            return False
        else:  # multiplierSequential == switch_multiplierSequential:
            if multiplier < switch_multiplier:
                return True
            else:
                return False

    def calcMultiplier(self, box: Tuple[numpy.ndarray, numpy.ndarray]):
        index = 2 if self.isStudio else 0
        sizeBox = box[1][index] - box[0][index] + self.securityDistance.layerByLayer  # expand by security distance

        sizeBuildPlate = self.machineSize.max_y if self.isStudio else self.machineSize.max_x

        multiplierLayerByLayer = int(sizeBuildPlate/sizeBox)
        multiplierSequential = self.calcMultiplierSequential(box)

        return multiplierLayerByLayer * multiplierSequential

    def calcMultiplierSequential(self, box: Tuple[numpy.ndarray, numpy.ndarray]):
        index = 0 if self.isStudio else 2

        sizeBox = box[1][index] - box[0][index] + self.securityDistance.layerByLayer + self.securityDistance.distance  # expand by security distance
        sizeBuildPlate = self.machineSize.max_x if self.isStudio else self.machineSize.max_y

        return int((sizeBuildPlate + self.securityDistance.distance)/sizeBox)

    def _lengthX(self, box: Tuple[numpy.ndarray, numpy.ndarray]) -> numpy.float64:
        index = 2 if self.isStudio else 0  # for some reason the cura orientation is a bit strange
        return abs((box[1] - box[0])[index])

    def _lengthY(self, box: Tuple[numpy.ndarray, numpy.ndarray]) -> numpy.float64:
        index = 0 if self.isStudio else 2  # for some reason the cura orientation is a bit strange
        return abs((box[1] - box[0])[index])

    def _extractTranslationsWithOffset(self, slotY, bbox_list: List[Tuple[numpy.ndarray, numpy.ndarray]], secDist) -> List[numpy.ndarray]:
        org = numpy.array([self.machineSize.max_x/2.0, 0, self.machineSize.max_y/2.0], dtype=numpy.float64)

        translations = [None] * len(bbox_list)
        lastYCoordinate = self.securityDistance.layerByLayer / 2.0
        for yItem in slotY:
            yCoordinate = yItem.endY
            lastXCoordinate = self.securityDistance.layerByLayer / 2.0
            for xItem in yItem.itemsX:
                xCoordinate = xItem.endX - secDist
                bbox = bbox_list[xItem.bboxCounter]
                if self.isStudio:
                    newMax = numpy.array([self.machineSize.max_x - lastYCoordinate, bbox[1][1], self.machineSize.max_y - lastXCoordinate], dtype=numpy.float64)
                else:
                    newMax = numpy.array([xCoordinate, bbox[1][1], self.machineSize.max_y - lastYCoordinate], dtype=numpy.float64)

                translation = newMax - bbox[1] - org
                translations[xItem.bboxCounter] = translation
                lastXCoordinate = xCoordinate + self.securityDistance.layerByLayer

            lastYCoordinate = yCoordinate + self.securityDistance.layerByLayer

        return translations

    def _adustTranslations(self, translations: List[numpy.ndarray], bboxes, overflow: bool) -> List[numpy.ndarray]:
        def calcGlobalBBox(translations: List[numpy.ndarray], bboxes) -> Tuple[numpy.ndarray, numpy.ndarray]:
            minCoordinate = bboxes[0][0] + translations[0]
            maxCoordinate = bboxes[0][1] + translations[0]
            for counter in range(1, len(translations)):
                minCoordinate = numpy.minimum(minCoordinate, bboxes[counter][0] + translations[counter])
                maxCoordinate = numpy.maximum(maxCoordinate, bboxes[counter][1] + translations[counter])

            return (minCoordinate, maxCoordinate)

        globalBBox = calcGlobalBBox(translations, bboxes)

        xDist = 0
        yDist = 0
        if self.isStudio:
            xDist = 0.5 * self.machineSize.max_x + globalBBox[0][0] - self.securityDistance.object  # bbox coordinates are +-0.5*self.machineSize.max_x
            xDist = -min(self.preferedStartPoint[0], xDist / 2.0)
        else:
            if not overflow:
                xDist = 0.5 * self.machineSize.max_x - globalBBox[1][0] - self.securityDistance.object  # bbox coordinates are +-0.5*self.machineSize.max_x
                xDist = min(self.preferedStartPoint[0], xDist / 2.0)

        if not self.isStudio or not overflow:
            yDist = 0.5 * self.machineSize.max_y + globalBBox[0][2] - 2.0 * self.securityDistance.object  # bbox coordinates are +-0.5*self.machineSize.max_x
            yDist = -min(self.preferedStartPoint[1], yDist / 2.0)

        if self.tandemMode:
            xDist -= self.machineSize.max_x / 2

        translationsOffset = numpy.array([xDist, 0, yDist])
        for translation in translations:
            translation += translationsOffset

        return translations

    def _slotYMax(self):
        if self.isStudio:
            return self.machineSize.max_x + self.securityDistance.distance - self.securityDistance.layerByLayer/2
        else:
            return self.machineSize.max_y + self.securityDistance.distance - self.securityDistance.layerByLayer/2

    def _itemXMax(self):
        if self.isStudio:
            return self.machineSize.max_y
        else:
            return self.machineSize.max_x

    def _createBBoxListEnhanced(self, bbox_list: List[Tuple[numpy.ndarray, numpy.ndarray]]):
        def expandBox(box: Tuple[numpy.ndarray, numpy.ndarray], val: float) -> Tuple[numpy.ndarray, numpy.ndarray]:
            expandVec = numpy.array([val, 0.0, val], dtype=numpy.float64)
            box1 = box[1] + expandVec
            return (box[0], box1)

        bbox_list_enhanced = [(self._lengthY(expandBox(bbox, self.securityDistance.layerByLayer)), expandBox(bbox, self.securityDistance.layerByLayer), counter)
                              for counter, bbox in enumerate(bbox_list)]
        list.sort(bbox_list_enhanced, reverse=True, key=lambda x: x[0])

        return bbox_list_enhanced

    def _createSlotY(self, bbox_list_enhanced) -> Tuple[List[SlotY_item], bool]:
        def getLastLengthY(slotY, slotY_counter):
            return slotY[slotY_counter].endY

        def getLastLengthX(slotY, slotY_counter):
            return slotY[slotY_counter].itemsX[-1][0]

        studioFirstSecurityDistance = self.securityDistance.distance - self.securityDistance.layerByLayer/2

        slotY = [SlotY_item(endY=bbox_list_enhanced[0][0] + studioFirstSecurityDistance, itemsX=[ItemX_item(
            endX=self._lengthX(bbox_list_enhanced[0][1]), bboxCounter=bbox_list_enhanced[0][2])])]
        slotY_counter = 1

        bboxCounter = 1
        notInsertedCount = 0
        while bboxCounter < len(bbox_list_enhanced):
            bboxCounter_old = bboxCounter
            lengthAndBoxAndCounter = bbox_list_enhanced[bboxCounter]

            lengthX = self._lengthX(lengthAndBoxAndCounter[1])

            # Check if slotY can be extended in y direction
            if slotY_counter == len(slotY):
                newLastLengthY = lengthAndBoxAndCounter[0] + self.securityDistance.distance + getLastLengthY(slotY, slotY_counter - 1)
                if newLastLengthY < self._slotYMax():  # create a new slot
                    slotY.append(SlotY_item(endY=newLastLengthY, itemsX=[ItemX_item(
                        endX=lengthX, bboxCounter=lengthAndBoxAndCounter[2])]))
                    slotY_counter += 1
                    bboxCounter += 1
                else:
                    slotY_counter = 0
            else:
                newLastLengthX = getLastLengthX(slotY, slotY_counter) + lengthX
                if newLastLengthX < self._itemXMax():
                    slotY[slotY_counter].itemsX.append(ItemX_item(
                        endX=newLastLengthX, bboxCounter=lengthAndBoxAndCounter[2]))
                    bboxCounter += 1
                slotY_counter += 1

            # if the build plate is full, just place the rest of the item in the first slot.
            if bboxCounter == bboxCounter_old:
                notInsertedCount += 1
                if notInsertedCount > len(slotY):
                    for invalidCounter in range(bboxCounter, len(bbox_list_enhanced)):
                        lengthAndBoxAndCounter = bbox_list_enhanced[invalidCounter]
                        lengthX = self._lengthX(lengthAndBoxAndCounter[1])
                        newLastLengthX = getLastLengthX(slotY, 0) + lengthX
                        slotY[0].itemsX.append(ItemX_item(endX=newLastLengthX, bboxCounter=lengthAndBoxAndCounter[2]))
                    return slotY, True
            else:
                notInsertedCount = 0

        return slotY, False

    def process(self, bbox_list) -> Tuple[List[numpy.ndarray], bool]:
        """Does the arrangement."""
        bbox_list_enhanced = self._createBBoxListEnhanced(bbox_list)
        slotY, warning = self._createSlotY(bbox_list_enhanced)
        translations = self._extractTranslationsWithOffset(slotY, bbox_list, self.securityDistance.layerByLayer / 2.0)
        translations = self._adustTranslations(translations, bbox_list, warning)
        return translations, warning
