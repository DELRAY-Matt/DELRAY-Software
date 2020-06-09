# coding=utf-8

# Copyright (c) 2020 BigRep GmbH

from . import ProHMIUpdateChecker


def getMetaData():
    return {}


def register(app):
    return {"extension": ProHMIUpdateChecker.ProHMIUpdateChecker()}
