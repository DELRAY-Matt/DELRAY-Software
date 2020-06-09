# Copyright (c) 2020 BigRep GmbH
# Blade Updater plugin is released under the terms of the LGPLv3.

from UM.Logger import Logger
from UM.Extension import Extension
from UM.Application import Application
from UM.Version import Version
from UM.Message import Message
from UM.i18n import i18nCatalog

from . import updaterScript

i18n_catalog = i18nCatalog("BladeUpdater")

class BladeUpdater(Extension):
    def __init__(self):
        super().__init__()
        self.addMenuItem("Update Configuration", self.manualUpdater)
        self._message = None

        self.currentVersion = str(Version(Application.getInstance().getVersion())).split("-")[0]
        self.pluginPath = "plugins/BladeUpdater/"

    def manualUpdater(self):
        status = updaterScript.manualUpdate(self.currentVersion, self.pluginPath)
        Logger.log("d", "Status: %s", status)

        if self._message:
            self._message.hide()

        self._message = Message(i18n_catalog.i18nc("@info:status", str(status)), title=i18n_catalog.i18nc("@info:title", "Blade Updater"))
        self._message.show()

    def startUpdater(self):
        status = updaterScript.main(self.currentVersion, self.pluginPath)
        Logger.log("d", "Status: %s", status)
