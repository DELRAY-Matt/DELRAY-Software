# Copyright (c) 2019 BigRep
# The Batch Printing plugin is released under the terms of the LGPLv3.

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("BatchPrintingPlugin")

from . import BatchPrintingPlugin

def getMetaData():
    return {}


def register(app):
    return {"extension": BatchPrintingPlugin.BatchPrintingPlugin()}
