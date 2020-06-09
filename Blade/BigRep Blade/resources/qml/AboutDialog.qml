// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

// Modified by BigRep 2019

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Window 2.1

import UM 1.1 as UM
import Cura 1.1 as Cura


UM.Dialog
{
    id: base

    //: About dialog title
    title: catalog.i18nc("@title:window","About BigRep Blade")

    minimumWidth: 500 * screenScaleFactor
    minimumHeight: 650 * screenScaleFactor
    width: minimumWidth
    height: minimumHeight

    Image
    {
        id: logo
        width: (base.minimumWidth * 0.85) | 0
        height: width * (1/3.31) | 0

        source: UM.Theme.getImage("logo")

        sourceSize.width: width
        anchors.top: parent.top
        anchors.topMargin: ((base.minimumWidth - width) / 2) | 0
        anchors.horizontalCenter: parent.horizontalCenter

        UM.I18nCatalog{id: catalog; name:"cura"}
    }

    Label
    {
        id: version

        text: catalog.i18nc("@label","version: %1").arg(UM.Application.version)
        font: UM.Theme.getFont("large")
        anchors.right : logo.right
        anchors.top: logo.bottom
        anchors.topMargin: (UM.Theme.getSize("default_margin").height / 2) | 0
    }

    Label
    {
        id: description
        width: parent.width

        //: About dialog application description
        text: catalog.i18nc("@label","End-to-end solution for fused filament 3D printing.")
        font: UM.Theme.getFont("system")
        wrapMode: Text.WordWrap
        anchors.top: version.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
    }

    Label
    {
        id: creditsNotes
        width: parent.width

        //: About dialog application author note
        text: catalog.i18nc("@info:credit","BigRep Blade is developed on top of Cura by Ultimaker B.V.\nIt proudly uses the following projects:")
        font: UM.Theme.getFont("system")
        wrapMode: Text.WordWrap
        anchors.top: description.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
    }

    ScrollView
    {
        anchors.top: creditsNotes.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height

        width: parent.width
        height: base.height - y - (2 * UM.Theme.getSize("default_margin").height + closeButton.height)

        ListView
        {
            id: projectsList

            width: parent.width

            delegate: Row
            {
                Label
                {
                    text: "<a href='%1' title='%2'>%2</a>".arg(model.url).arg(model.name)
                    width: (projectsList.width * 0.25) | 0
                    elide: Text.ElideRight
                    onLinkActivated: Qt.openUrlExternally(link)
                }
                Label
                {
                    text: model.description
                    elide: Text.ElideRight
                    width: (projectsList.width * 0.6) | 0
                }
                Label
                {
                    text: model.license
                    elide: Text.ElideRight
                    width: (projectsList.width * 0.15) | 0
                }
            }
            model: ListModel
            {
                id: projectsModel
            }
            Component.onCompleted:
            {
                projectsModel.append({ name:"BigRep Blade", description: catalog.i18nc("@label", "Customization Layer"), license: "LGPLv3", url: "https://bigrep.com/blade/releases/" });
                projectsModel.append({ name:"Cura", description: catalog.i18nc("@label", "Graphical user interface"), license: "LGPLv3", url: "https://github.com/Ultimaker/Cura" });
                projectsModel.append({ name:"Uranium", description: catalog.i18nc("@label", "Application framework"), license: "LGPLv3", url: "https://github.com/Ultimaker/Uranium" });
                projectsModel.append({ name:"CuraEngine", description: catalog.i18nc("@label", "G-code generator"), license: "AGPLv3", url: "https://github.com/Ultimaker/CuraEngine" });
                projectsModel.append({ name:"libArcus", description: catalog.i18nc("@label", "Interprocess communication library"), license: "LGPLv3", url: "https://github.com/Ultimaker/libArcus" });
                projectsModel.append({ name:"Auto-Orientation", description: catalog.i18nc("@label", "Cura plugin for auto orientation"), license: "LGPLv3", url: "https://github.com/nallath/CuraOrientationPlugin" });
                projectsModel.append({ name:"Custom Support", description: catalog.i18nc("@label", "Cura plugin for custom support"), license: "LGPLv3", url: "https://github.com/lokster/cura-custom-supports" });

                projectsModel.append({ name:"Python", description: catalog.i18nc("@label", "Programming language"), license: "Python", url: "http://python.org/" });
                projectsModel.append({ name:"Qt5", description: catalog.i18nc("@label", "GUI framework"), license: "LGPLv3", url: "https://www.qt.io/" });
                projectsModel.append({ name:"PyQt", description: catalog.i18nc("@label", "GUI framework bindings"), license: "RIVERBANK commercial license", url: "https://riverbankcomputing.com/software/pyqt" });
                projectsModel.append({ name:"SIP", description: catalog.i18nc("@label", "C/C++ Binding library"), license: "RIVERBANK COMPUTING LIMITED LICENSE AGREEMENT FOR SIP 4.8", url: "https://riverbankcomputing.com/software/sip" });
                projectsModel.append({ name:"Protobuf", description: catalog.i18nc("@label", "Data interchange format"), license: "BSD", url: "https://developers.google.com/protocol-buffers" });
                projectsModel.append({ name:"SciPy", description: catalog.i18nc("@label", "Support library for scientific computing"), license: "BSD-new", url: "https://www.scipy.org/" });
                projectsModel.append({ name:"NumPy", description: catalog.i18nc("@label", "Support library for faster math"), license: "BSD", url: "http://www.numpy.org/" });
                projectsModel.append({ name:"NumPy-STL", description: catalog.i18nc("@label", "Support library for handling STL files"), license: "BSD", url: "https://github.com/WoLpH/numpy-stl" });
                projectsModel.append({ name:"Shapely", description: catalog.i18nc("@label", "Support library for handling planar objects"), license: "BSD", url: "https://github.com/Toblerity/Shapely" });
                projectsModel.append({ name:"Trimesh", description: catalog.i18nc("@label", "Support library for handling triangular meshes"), license: "MIT", url: "https://trimsh.org" });
                projectsModel.append({ name:"NetworkX", description: catalog.i18nc("@label", "Support library for analysis of complex networks"), license: "3-clause BSD", url: "https://networkx.github.io/" });
                projectsModel.append({ name:"libSavitar", description: catalog.i18nc("@label", "Support library for handling 3MF files"), license: "LGPLv3", url: "https://github.com/ultimaker/libsavitar" });
                projectsModel.append({ name:"libCharon", description: catalog.i18nc("@label", "Support library for file metadata and streaming"), license: "LGPLv3", url: "https://github.com/ultimaker/libcharon" });
                projectsModel.append({ name:"PySerial", description: catalog.i18nc("@label", "Serial communication library"), license: "Python", url: "http://pyserial.sourceforge.net/" });
                projectsModel.append({ name:"python-zeroconf", description: catalog.i18nc("@label", "ZeroConf discovery library"), license: "LGPL", url: "https://github.com/jstasiak/python-zeroconf" });
                projectsModel.append({ name:"Clipper", description: catalog.i18nc("@label", "Polygon clipping library"), license: "Boost", url: "http://www.angusj.com/delphi/clipper.php" });
                projectsModel.append({ name:"rapidJSON", description: catalog.i18nc("@label", "Support for json files"), license: "Boost", url: "https://github.com/Tencent/rapidjson" });
                projectsModel.append({ name:"STB", description: catalog.i18nc("@label", "single-file headers"), license: "MIT", url: "https://https://github.com/nothings/stb" });
                projectsModel.append({ name:"Requests", description: catalog.i18nc("@Label", "Python HTTP library"), license: "LGPLv3", url: "https://pypi.org/project/requests/" });

                projectsModel.append({ name:"Noto Sans", description: catalog.i18nc("@label", "Font"), license: "Apache 2.0", url: "https://www.google.com/get/noto/" });
                projectsModel.append({ name:"Font-Awesome-SVG-PNG", description: catalog.i18nc("@label", "SVG icons"), license: "SIL OFL 1.1", url: "https://github.com/encharm/Font-Awesome-SVG-PNG" });
                projectsModel.append({ name:"AppImageKit", description: catalog.i18nc("@label", "Linux cross-distribution application deployment"), license: "MIT", url: "https://github.com/AppImage/AppImageKit" });
            }
        }
    }

    rightButtons: Button
    {
        //: Close about dialog button
        id: closeButton
        text: catalog.i18nc("@action:button","Close");

        onClicked: base.visible = false;
    }
    leftButtons: Button
    {
        text: "Show EULA"
        onClicked: {
            var url = "../../EULA.txt"
            Qt.openUrlExternally(url)
        }
    }
}
