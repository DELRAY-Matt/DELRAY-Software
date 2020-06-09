# Copyright (c) 2019 BigRep
# The Batch Printing plugin is released under the terms of the LGPLv3.

from UM.Scene.Iterator.Iterator import Iterator
from UM.Scene.SceneNode import SceneNode
from cura.CuraApplication import CuraApplication

class BatchIterator(Iterator):

    def __init__(self, scene_node):
        self._global_stack = CuraApplication.getInstance().getGlobalContainerStack()
        self._original_node_list = []

        super().__init__(scene_node)  # Call super to make multiple inheritance work.


    def _fillStack(self):
        for node in self._scene_node.getChildren():
            if not issubclass(type(node), SceneNode):
                continue

            convex_hull = node.callDecoration("getConvexHull")
            if convex_hull:
                self._node_stack.append(node)
