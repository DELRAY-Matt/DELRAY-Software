# coding=utf-8

# Copyright (c) 2020 BigRep GmbH

from UM.Application import Application
from UM.Message import Message
from UM.Version import Version
from UM.Logger import Logger
from UM.Job import Job

import urllib.request
import platform
import json
import codecs

from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("uranium")


##  This job checks if there is an update available on the provided URL.
class ProHMIUpdateCheckerJob(Job):
    def __init__(self, silent = False, url = None, callback = None, set_download_url_callback = None):
        super().__init__()
        self.silent = silent
        self._url = url
        self._callback = callback
        self._set_download_url_callback = set_download_url_callback
        self.application_name = "BigRep PRO HMI"

    def run(self):
        if not self._url:
            Logger.log("e", "Can not check for a new release. URL not set!")
        no_new_version = True


        Logger.log("i", "Checking for new version of %s" % self.application_name)
        try:
            headers = {"User-Agent": "%s - %s" % (self.application_name, Application.getInstance().getVersion())}
            request = urllib.request.Request(self._url, headers = headers)
            latest_version_file = urllib.request.urlopen(request)
        except Exception as e:
            Logger.log("w", "Failed to check for new version: %s" % e)
            if not self.silent:
                Message(i18n_catalog.i18nc("@info", "Could not access update information."),
                    title = i18n_catalog.i18nc("@info:title", "Version Upgrade")
                ).show()
            return

        try:
            reader = codecs.getreader("utf-8")
            data = json.load(reader(latest_version_file))

            if self.application_name in data:
                for key, value in data[self.application_name].items():
                    if "major" in value and "minor" in value and "revision" in value and "url" in value:
                        preferences = Application.getInstance().getPreferences()
                        latest_version_shown = preferences.getValue("info/latest_update_version_shown_bigrep_pro_hmi")
                        os = key
                        if platform.system() == os: #TODO: add architecture check
                            newest_version = Version([int(value["major"]), int(value["minor"]), int(value["revision"])])
                            if latest_version_shown < newest_version:
                                preferences = Application.getInstance().getPreferences()
                                preferences.setValue("info/latest_update_version_shown_bigrep_pro_hmi", str(newest_version))
                                Logger.log("i", "Found a new version of BigRep PRO HMI. Spawning message")
                                self.showUpdate(newest_version, value["url"])
                                no_new_version = False
                                break
                    else:
                        Logger.log("w", "Could not find version information or download url for update.")
            else:
                Logger.log("w", "Did not find any version information for %s." % self.application_name)
        except Exception:
            Logger.logException("e", "Exception in update checker while parsing the JSON file.")
            Message(i18n_catalog.i18nc("@info", "An error occurred while checking for updates."), title = i18n_catalog.i18nc("@info:title", "Error")).show()
            no_new_version = False  # Just to suppress the message below.

        if no_new_version and not self.silent:
            Message(i18n_catalog.i18nc("@info", "No new version was found."), title = i18n_catalog.i18nc("@info:title", "Version Upgrade")).show()

    def showUpdate(self, newest_version: Version, download_url: str) -> None:
        title_message = i18n_catalog.i18nc("@info:status","{application_name} {version_number} is available!".format(application_name = self.application_name, version_number = newest_version))
        content_message = i18n_catalog.i18nc("@info:status","{application_name} {version_number} provides a better and more reliable printing experience.".format(application_name = self.application_name, version_number = newest_version))

        message = Message(text = content_message, title = title_message)
        message.addAction("download", i18n_catalog.i18nc("@action:button", "Download"), "[no_icon]", "[no_description]")

        message.addAction("new_features", i18n_catalog.i18nc("@action:button", "Learn more about the new features"), "[no_icon]", "[no_description]",
                          button_style = Message.ActionButtonStyle.LINK,
                          button_align = Message.ActionButtonStyle.BUTTON_ALIGN_LEFT)

        if self._set_download_url_callback:
            self._set_download_url_callback(download_url)
        message.actionTriggered.connect(self._callback)
        message.show()