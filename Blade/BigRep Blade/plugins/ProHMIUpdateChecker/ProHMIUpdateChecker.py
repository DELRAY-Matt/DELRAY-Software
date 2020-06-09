# coding=utf-8

# Copyright (c) 2020 BigRep GmbH

import os
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

from typing import Set

from UM.Extension import Extension
from UM.Application import Application
from UM.Logger import Logger
from UM.i18n import i18nCatalog
from UM.Settings.ContainerRegistry import ContainerRegistry

from cura.Settings.GlobalStack import GlobalStack

from .ProHMIUpdateCheckerJob import ProHMIUpdateCheckerJob

i18n_catalog = i18nCatalog("cura")


## This Extension checks for new versions of the firmware based on the latest checked version number.
#  The plugin is currently only usable for applications maintained by Ultimaker. But it should be relatively easy
#  to change it to work for other applications.
class ProHMIUpdateChecker(Extension):
    url = "https://bigrep.com/wp-content/uploads/Blade/latest.json"
    # url = "https://support.bigrep.com/wp-content/uploads/latest_beta.json"

    def __init__(self) -> None:
        super().__init__()

        # Listen to a Signal that indicates a change in the list of printers, just if the user has enabled the
        # "check for updates" option
        Application.getInstance().getPreferences().addPreference("info/automatic_update_check", True)
        if Application.getInstance().getPreferences().getValue("info/automatic_update_check"):
            ContainerRegistry.getInstance().containerAdded.connect(self._onContainerAdded)

        self._check_job = None
        self._checked_printer_names = set()  # type: Set[str]

        # Which version was the latest shown in the version upgrade dialog. Don't show these updates twice.
        Application.getInstance().getPreferences().addPreference("info/latest_update_version_shown_bigrep_pro_hmi", "0.0.0")


    def _onContainerAdded(self, container):
        # Only take care when a new GlobalStack was added
        if isinstance(container, GlobalStack):
            self.checkFirmwareVersion(container, True)

    def _onJobFinished(self, *args, **kwargs):
        self._check_job = None

    ##  Connect with software.ultimaker.com, load latest.version and check version info.
    #   If the version info is different from the current version, spawn a message to
    #   allow the user to download it.
    #
    #   \param silent type(boolean) Suppresses messages other than "new version found" messages.
    #                               This is used when checking for a new firmware version at startup.
    def checkFirmwareVersion(self, container = None, silent = False):
        container_name = container.definition.getName()
        if container_name in self._checked_printer_names:
            return
        self._checked_printer_names.add(container_name)

        if container_name == "BigRep PRO":
            job = ProHMIUpdateCheckerJob(silent, self.url, self._onActionTriggeredHMI, self._onSetDownloadUrlHMI)
            job.start()

    def _onSetDownloadUrlHMI(self, download_url):
        self._download_url_hmi = download_url

    ##  Callback function for the "download" button on the update notification.
    #   This function is here is because the custom Signal in Uranium keeps a list of weak references to its
    #   connections, so the callback functions need to be long-lived. The UpdateCheckerJob is short-lived so
    #   this function cannot be there.

    def _onActionTriggeredHMI(self, message, action):
        if action == "download":
            if self._download_url_hmi is not None:
                QDesktopServices.openUrl(QUrl(self._download_url_hmi))
        elif action == "new_features":
            QDesktopServices.openUrl(QUrl(Application.getInstance().change_log_url))
