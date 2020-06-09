// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.4

import UM 1.3 as UM

import Cura 1.1 as Cura


UM.Dialog
{
    id: baseDialog
    minimumWidth: Math.round(UM.Theme.getSize("modal_window_minimum").width * 0.75)
    minimumHeight: Math.round(UM.Theme.getSize("modal_window_minimum").height * 0.5)
    width: minimumWidth
    height: minimumHeight
    title: catalog.i18nc("@title:window", "User Agreement")

    TextArea
    {
        anchors.top: parent.top
        width: parent.width
        anchors.bottom: buttonRow.top
        text: ' <center><h3>END USER LICENSE AGREEMENT</h3></center>

Concluded between
<br>
<br>
<br>You, as the Licensee and Customer, as identified in the offer this License Agreement is attached to, hereinafter referred to as “Licensee” or “Customer”
<br>
<br>and
<br>
<br>BigRep GmbH, Gneisenaustraße 66, 10961 Berlin, Germany, hereinafter referred to as „Licensor“ or “BigRep”
<br>
<br>together referred to as the “Parties”
<br>
<br>1. Object of Contract
<br>This license agreement (hereinafter referred to as “Agreement”) establishes the terms for the license to use the BigRep Blade, which is defined in the User Documentation (available at $InstallDir$\Documentation\home.html). The Blade Software is composed of, communicates with, uses, and/or embeds different third party software. Licensee is, subject to the terms and conditions of this Agreement, entitled to use the Blade Software as such and in its entirety, in accordance with the User Documentation. The contained, embedded and/or otherwise used third party software is made available to Licensee subject to certain conditions, all of which are outlined in a separate document called “Third Party Software License Terms”, which forms an integral part of and is accepted by Licensee upon signature of this Agreement.
<br>
<br>2. Effective Date
<br>The Licensee agrees to the terms of this Agreement and the Third Party Software License Terms by executing the present License Agreement, however by running the Blade Software at the latest.
<br>
<br>3. License to use the Blade Software
<br>Blade Software is made available to Licensee under the terms of the GNU LESSER GENERAL PUBLIC LICENSE, Version 3, 29 June 2007. The relevant source code is available at https://bigrep.com/blade/releases.
<br>Licensee should have received a copy of the GNU General Public License Version 3, 29 June 2007, as well as the GNU LESSER GENERAL PUBLIC LICENSE, Version 3, 29 June 2007, along with this program.  If not, see https://www.gnu.org/licenses/.
<br>
<br>4. Licensee’s use and obligations
<br>Blade Software may be used in the manner and to the extent as defined in the User Documentation, Section “Intended Use”, only. Blade Software was programmed and designed to run and function on/with certain systems and devices, and/or subject to specific technical preconditions. The functions and features of Blade Software as described in the User Documentation are available and run correctly only if and to the extent Licensee complies with the “Software Use Preconditions” established in the User Documentation, Section “Requirements/First Steps“.
<br>
<br>5. Material Defects
<br>For the duration of 12 months from downloading and installing Blade Software by Licensee, BigRep shall be liable for material defects and defects of title which have existed on the delivery date to the extent as defined hereinafter. A material defect exists if the Blade Software does not run and/or allow the functions as described in the “User Documentation”, if and to the extent the Blade Software is used and run in the recommended environment and in accordance with the Software Use Preconditions, and if and to the extent the alleged defect is reproducible. Any expressed or implied warranty or commitment, including the warranties of marketable quality or usually assumed properties and/or the fitness for particular purposes, is disclaimed. Insignificant defects not impairing the functioning are expressively excluded from the defects’ liability.
<br>
<br>Any material defect of the Blade Software shall be notified to BigRep within a reasonable period of time, yet no later than 10 days after the defect occurred. Any notification must be made in writing and describe the defect in a manner that allows BigRep to evaluate and decide whether this defect triggers BigRep’s liability for material defects. BigRep shall have at least two opportunities to correct that defect by defect remedy or subsequent delivery of an error-free program version. For the purpose of remedy of defects, Licensee shall enable BigRep to remote access the Blade Software to the extent and for the period as necessary. Claims for damages of the Licensee or reimbursement of frustrated expenses are subject to the limitations in Article 4.4 below. Further claims of the Licensee are excluded.
<br>
<br>6. Defects of title
<br>BigRep confirms that BigRep has programmed Blade Software itself, by using the Third Party Software mentioned in the Third Party Software License Terms. BigRep does, however, not assume any responsibility or liability for/in case of a possible third party rights infringements, to any other extent than stated in this paragraph:
<br>Should a competent court find, finally and bindingly, that Licensee is infringing a third party’s rights when using the Blade Software in accordance with the User Documentation, Licensee undertakes to notify BigRep immediately.  BigRep will evaluate the allegations and, in BigRep’s discretion and at its expense,
<br>(a)	provide the Licensee with the necessary use rights, or
<br>(b)	re-design the Blade Software in a manner as to no longer infringe upon the relevant third party rights, or
<br>(c)	recommend Licensee to stop using Blade Software and reimburse the Licensee for the license fee paid (minus an appropriate compensation for use), if BigRep cannot achieve any other redress with reasonable effort.
<br>
<br>Unless contrary to mandatory applicable laws, this defects liability is exclusive and final, whereas Licensee shall not have the right to any other claims or means.
<br>
<br>7. Fault-based liability 
<br>Within the scope of fault-based liability BigRep is liable for damages - for whatever legal reason - in cases of intent and gross negligence. In case of simple negligence BigRep is liable, subject to a milder liability standard according to legal provisions (e.g. for diligence in one’s own affairs), only
<br>a) for damages resulting from death or injury of body or health, personal injury,
<br>b) for damages arising from the not immaterial breach of a fundamental contractual duty (which is an obligation without which proper performance of the contract would be impossible and on the performance of which the contractual partner regularly relies and is entitled to rely); in this event, however, the liability of BigRep to compensate for damages is limited to the foreseeable damages that would typically have occurred. 
<br>
<br>All other claims of Licensee based on contract or tort are excluded. For this reason, BigRep is not liable for damage that did not occur to the Blade Software as such; in particular, BigRep does neither assume liability for consequential damages, defect damages (“Mangelschaden”), futile expenditures, indirect damages and/or purely financial loss (i.e. loss without damage to any absolute rights), nor for loss of interest, legal costs and further related costs. This shall not apply in case of personal injury, and/or if the damage is caused by BigRep intentionally or by gross negligence. 
<br>
<br>In particular, BigRep shall only be liable for direct damages caused by such malfunctions of the Blade Software, which were caused by BigRep with at least gross negligence. Furthermore, BigRep shall only be liable for direct damages which occur when Blade Software is used in accordance with the Software Use Preconditions. 
<br>
<br>The limitations of liability arising from the above Articles do not apply to claims of the Customer under the German Product Liability Act (Produkthaftungsgesetz) and/or if BigRep has fraudulently concealed defects or given a guarantee for the condition and quality of the goods. 
<br>
<br>8. Third Party Software
<br>Blade Software contains software from third party producers, including open source software. Such “Third Party Software” is specified in the Third Party Software License Terms as available in “Blade Installation directory\licences.txt”, which can be accessed in the Blade Software via the menu entry “Help/About…”. Licensee explicitly confirms his awareness of the respective specific terms by executing the present License Agreement, however by putting into operation the respective device containing the BigRep Software and Third Party Software at the latest.
<br>
<br>9. Bug-Fixing
<br>From time to time and as may be reasonable, BigRep may make available hot-fixes, service-packs and/or similar updates (hereinafter together referred to as “Update”) to correct possible failures of the Blade Software to Licensee and notify Licensee in an appropriate manner. Licensee is obliged to install the respective Update within 14 days after receipt of the notification. Should Licensee fail to install the Update in time, BigRep shall be released from any defects and/or other liability to the extent such liability would not have occurred if the respective Update had been installed in time. Unless agreed otherwise, these Updates are provided to Licensee under the terms of this Agreement, regardless of whether a respective reference is made in each individual case.
<br>
<br>Unless explicitly agreed in writing, service and/or support of Blade Software – thus services beyond the said Updates and/or possible activities under defects liability (section 4.2) – are offered and provided by BigRep subject to separate terms and conditions and the applicable fees. 
<br>
<br>10. Miscellaneous 
<br>Each amendment and supplement to this agreement must be in writing. 
<br>
<br>Should one or several terms of this agreement be invalid, the remaining terms of this agreement will remain in force and effective. An ineffective condition is to be replaced with a new one which serves the economic purpose of the invalid or unenforceable clause as closely as possible. In the event of a dispute, the Contract Partner’s to the agreement shall first try to reach a valid resolution of the dispute.
<br>
<br>11. Venue and applicable law
<br>This agreement is governed by German law. United Nations Convention on the International Sale of Goods (CISG) and the provisions of the law on conflict of laws under international private law are explicitly excluded. 
<br>
<br>If Licensee’s permanent registered office is in an EU Member State, Iceland, Norway or Switzerland, any and all legal disputes arising from and/or in connection with the Contract Partners’ business relationship under this Agreement and/or the present Agreement, including, in particular, its conclusion, validity, violation and/or termination, shall exclusively be settled by the competent court in Innsbruck, Austria. 
<br>
<br>If Licensee’s permanent registered office is in any other State, any and all legal disputes arising from and/or in connection with the Contract Partners’ business relationship under this Agreement and/or the present Agreement, including, in particular, its conclusion, validity, violation and/or termination, shall be finally settled under the Rules of Arbitration of the International Chamber of Commerce (ICC) by one arbitrator appointed by BigRep and the Licnesee mutually, in lack of an agreement appointed in accordance with the said Rules. The arbitration shall be held in Vienna, Austria. The language to be used in the arbitral proceedings shall be German. 
<br>
<br>The award shall be final and binding and BigRep and Licensee waive any possible right to appeal the same before any national, supra- or international state and/or other courts and/or authorities. Regardless of this arbitration clause, BigRep reserves the right to seek injunctive relief/exercise the right of prohibition, seek preliminary injunction/interim measures, and/or make other claims suitable in view of safeguarding the rights of BigRep, before any authorities – including but not limited to state courts –, in any jurisdiction and wherever located that BigRep deems appropriate. 

                '
        readOnly: true;
        textFormat: TextEdit.RichText

    }

    Item
    {
        id: buttonRow
        anchors.bottom: parent.bottom
        width: parent.width
        anchors.bottomMargin: UM.Theme.getSize("default_margin").height

        UM.I18nCatalog { id: catalog; name:"cura" }

        Button
        {
            anchors.left: parent.left 
            text: "Show Licences"
            onClicked: {
                var url = "../../licences.txt"
                Qt.openUrlExternally(url)
            }
        }

        Row
        {
            anchors.right: parent.right

            Button
            {
                // anchors.left: parent.left
                text: catalog.i18nc("@action:button", "I don't agree")
                onClicked: {
                    baseDialog.rejected()
                }
            }
            Button
            {
                // anchors.right: parent.right
                text: catalog.i18nc("@action:button", "I understand and agree")
                onClicked: {
                    baseDialog.accepted()
                }
            }
        }
    
    }

    onAccepted: manager.didAgree(true)
    onRejected: manager.didAgree(false)
    onClosing: manager.didAgree(false)
}
