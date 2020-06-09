# Copyright (c) 2020 BigRep GmbH
# Blade Updater plugin is released under the terms of the LGPLv3.

import os
import json
import shutil
import configparser

def getAllVersionFolders(bladeDataFiles):
    # Filtering all files/folder in BigRep Blade to get only versions back
    versionFolders = []
    for dataFile in bladeDataFiles:
        if "." in dataFile:
            fileCheck = dataFile.split(".")
            if fileCheck[0].isdigit() and fileCheck[1].isdigit(): 
                versionFolders.append(dataFile)

    return versionFolders

def getPreviousVersion(versionFolders, currentVersionFolder):
    relevantVersions = versionFolders

    # Removes the current version
    relevantVersions.remove(currentVersionFolder)

    # Sort the version, should not be necessary, but just in case
    relevantVersions.sort()
    
    # Removes all versions higher than current version
    versionsToRemove = []
    for version in relevantVersions:
        if version > currentVersionFolder:
            versionsToRemove.append(version)
    for version in versionsToRemove:
        relevantVersions.remove(version)

    # Checks if there no or only one version
    if relevantVersions is None:
        return None
    elif len(relevantVersions) == 1:
        return relevantVersions[0]

    # Since the List is sortet, we just return the last entry
    return str(relevantVersions[-1])

def copyOldVersion(currentVersionFolder, previousVersion, bladeDataPath):
    # We are trying to copy everything important from the old version to the new one.
    # Unfortunate the new folder has been already created with some files and folder.

    # List of files/folders(including files) we want to copy
    doCopyFile = ["BigRep Blade.cfg"]
    doCopyFolder = ["definition_changes", "extruders", "machine_instances", "materials", "quality",
                    "quality_changes", "scripts", "setting_visibility", "user", "variants"]
    
    if os.path.exists(os.path.join(bladeDataPath, currentVersionFolder) + "/BigRep Blade.cfg"):
        return None

    pathPreVer = os.path.join(bladeDataPath, previousVersion)
    pathCurVer = os.path.join(bladeDataPath, currentVersionFolder)

    for folder in os.listdir(pathCurVer):
        if folder in doCopyFolder:
            os.rmdir(os.path.join(pathCurVer, folder))

    for data in os.listdir(pathPreVer):
        if data in doCopyFolder:
            shutil.copytree(os.path.join(pathPreVer, data), os.path.join(pathCurVer, data))
        elif data in doCopyFile:
            shutil.copy(os.path.join(pathPreVer, data), os.path.join(pathCurVer, data))

    return True

def loadSettingsFile(currentVersionFolder, pluginPath):
    try:
        with open(pluginPath + "settings/"+currentVersionFolder+".json") as settingsFile:
            versionSettings = json.load(settingsFile)
        return versionSettings
    except FileNotFoundError:
        return None

def updateConfigs(versionSettings, currentVersionFolder, bladeDataPath):
    # Depending on what we want to update, we don't need to change every single file.
    # The most important files are inside the extruders folder which contain the whole train.
    # Currently we only changed quality and material names so far.
    # Things which should not be changed are machine id, variant, extruder. Blade Master told you so!!

    pathCurVer = os.path.join(bladeDataPath, currentVersionFolder)

    for configFile in os.listdir(os.path.join(pathCurVer, "extruders")):
        config = configparser.ConfigParser()
        config.read(os.path.join(pathCurVer, "extruders", configFile))

        # Update changed quality file names
        if config["containers"]["2"] in versionSettings["changedQualities"]:
            config["containers"]["2"] = versionSettings["changedQualities"][config["containers"]["2"]]

        # Update changed material file names
        selectedMaterial = "bigrep" + config["containers"]["3"].split("bigrep")[1][:-1]
        if selectedMaterial in versionSettings["changedMaterials"]:
            newMaterial = versionSettings["changedMaterials"][selectedMaterial]
            config["containers"]["3"] = config["containers"]["3"].replace(selectedMaterial, newMaterial)

        with open(os.path.join(pathCurVer, "extruders", configFile), 'w') as configFile:
            config.write(configFile)

    status = True
    return status

def manualUpdate(currentVersion, pluginPath=""):
    status = "If you see this message, an unknown error has occurred."

    currentVersionFolder = ".".join(currentVersion.split(".")[:-1])

    versionSettings = loadSettingsFile(currentVersionFolder, pluginPath)
    if versionSettings is None:
        status = "Error: Settings File not found."
        return status

    appdataPath = os.getenv("APPDATA")
    bladeDataPath = os.path.join(appdataPath, "BigRep Blade")

    status = updateConfigs(versionSettings, currentVersionFolder, bladeDataPath)

    if status:
        status = "Updating config files is done. Please restart Blade."

    return status


def main(currentVersion, pluginPath=""):
    status = None
    currentVersionFolder = ".".join(currentVersion.split(".")[:-1])

    versionSettings = loadSettingsFile(currentVersionFolder, pluginPath)
    if versionSettings is None:
        status = "Error: Settings File not Found."
        return status

    appdataPath = os.getenv("APPDATA")
    bladeDataPath = os.path.join(appdataPath, "BigRep Blade")

    # Fix in case the CurrentVersionFolder does not exsist in Blade folder, which it should.
    if not os.path.exists(os.path.join(bladeDataPath, currentVersionFolder)):
        os.mkdir(os.path.join(bladeDataPath, currentVersionFolder))

    bladeDataFiles = os.listdir(bladeDataPath)
    versionFolders = getAllVersionFolders(bladeDataFiles)

    previousVersion = getPreviousVersion(versionFolders, currentVersionFolder)
    if previousVersion is None:
        status = "No previous version found in Appdata"
        return status
    elif previousVersion not in versionSettings["validPreviousVersions"]:
        status = "Previous version is not valid for copying and updating"
        return status

    if versionSettings["copyPrevious"]:
        status = copyOldVersion(currentVersionFolder, previousVersion, bladeDataPath)
        if status is None:
            status = "Did not copy because 'BigRep Blade.cfg' already exist."
            return status

    if versionSettings["updatePrevious"] and status:
        status = updateConfigs(versionSettings, currentVersionFolder, bladeDataPath)
    else:
        status = "No Settings to update or copy was not succesful."
        return status

    return status

if __name__ == "__main__":
    status = main("2.2.0")
    print(status)
