# Copyright (c) 2020 BigRep
# The Blade Updater is released under the terms of the LGPLv3.

from . import BladeUpdater

def getMetaData():
    return {}

def register(app):
    return {"extension": BladeUpdater.BladeUpdater()}
