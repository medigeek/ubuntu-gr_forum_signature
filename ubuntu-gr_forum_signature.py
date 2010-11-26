#!/usr/bin/python
# -*- coding: utf-8 -*-
# File: ubuntu-gr_signature.py
# Purpose: Proposes a signature with useful hardware/software information to forum newcomers/newbies
# Requires: python 2.5, lshw, lsb-release, sudo (for motherboard chip recognition)

# DEBUG: sudo lshw -xml -sanitize | pastebinit -b "http://pastebin.com"

# Copyright (c) 2010 Savvas Radevic <vicedar@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

""" Example of signature:
Γνώσεις ⇛ Linux: � ┃ Προγραμματισμός: � ┃ Αγγλικά: �
Λειτουργικό: Ubuntu 10.10 64-bit (en_GB.utf8)
Προδιαγραφές ⇛ Intel Core 2 Duo E6550 2.33GHz │ RAM 2008 MiB │ MSI MS-7235
Κάρτες γραφικών: nVidia G73 [GeForce 7300 GT] [10DE:393]
Δίκτυα: Ethernet: Realtek RTL-8139/8139C/8139C+ [10EC:8139], Ethernet: Realtek RTL-8110SC/8169SC Gigabit Ethernet [10EC:8167]
"""

import sys

if sys.version < '2.5':
    sys.exit('ERROR: You need python 2.5 or higher to use this program.')
if sys.platform and sys.platform[0:5] != "linux":
    sys.exit('ERROR: This script is built for GNU/Linux platforms (for now)')

import subprocess
import os
import xml.dom.minidom
import re

class core():
    def __init__(self, fxml=""):
        self.unknown = u"�" # Character/string for unknown data
        self.lshwxml = ""
        self.lshwinfo = {
            "cpu": self.unknown,
            "memory": self.unknown,
            "display": list(self.unknown),
            "system": self.unknown,
            "core": self.unknown,
            "network": list(self.unknown),
        }
        self.lshw(fxml)
        self.knowledge()
        self.osinfo()
        self.specs()

    def knowledge(self):
        s = {   "linux": self.unknown,
                "programming": self.unknown,
                "english": self.unknown
            }
        print( u"Γνώσεις ⇛ Linux: %s ┃ Προγραμματισμός: %s ┃ Αγγλικά: %s" %
                (s["linux"], s["programming"], s["english"])
        )

    def osinfo(self):
        lines = self.getfile("/etc/lsb-release")
        distrib = dict()
        for l in lines:
            lx = l.split("=")
            if lx[0] == "DISTRIB_ID":
                distrib["id"] = lx[1].rstrip("\n")
            elif lx[0] == "DISTRIB_RELEASE":
                distrib["rel"] = lx[1].rstrip("\n")
        lang = self.oslang()
        arch_type = self.machinearch()
        print(u"Λειτουργικό: %s %s %s (%s)" % (distrib["id"], distrib["rel"],
            arch_type, lang))

    def specs(self):
        machine = self.shortenmachineid()
        print( u'Προδιαγραφές ⇛ %s │ RAM %s MiB │ %s\nΚάρτες γραφικών: %s\nΔίκτυα: %s' %
                (self.lshwinfo["cpu"],
                self.lshwinfo["memory"],
                machine,
                ', '.join(self.lshwinfo["display"]),
                ', '.join(self.lshwinfo["network"])
                )
        )

    def oslang(self):
        try:
            lang = os.environ["LANG"]
        except KeyError:
            # Assume en_US
            lang = "en_US"
        return lang  

    def machinearch(self):
        output = os.uname()[4]
        if output == "x86_64":
            mtype = "64-bit"
        elif re.match(r'i686|i386', output):
            mtype = "32-bit"
        else:
            mtype = "%s-bit" % self.unknown
        return mtype

    def shortenmachineid(self):
        # Shorten the machine/motherboard id and manufacturer
        if self.lshwinfo["system"] == self.lshwinfo["core"] and not self.lshwinfo["system"] == self.unknown:
            machine = self.lshwinfo["system"]
        elif self.lshwinfo["system"] == self.unknown and not self.lshwinfo["core"] == self.unknown:
            machine = self.lshwinfo["core"]
        elif not self.lshwinfo["system"] == self.unknown and self.lshwinfo["core"] == self.unknown:
            machine = self.lshwinfo["system"]
        else:
            machine = "%s - %s" % (self.lshwinfo["system"], self.lshwinfo["core"])
        return machine

    def shortenmoboid(self, tempa2):
        # Attempt to shorten motherboard chipset and company names
        if re.match(r'MICRO-STAR INTERNATIONAL', tempa2, re.IGNORECASE):
            temp_final2 = "MSI"
        elif re.match(r'Gigabyte Technology', tempa2, re.IGNORECASE):
            temp_final2 = "Gigabyte"
        elif re.match(r'ASUSTeK Computer', tempa2, re.IGNORECASE):
            temp_final2 = "ASUS"
        elif re.match(r'Intel Corporation', tempa2, re.IGNORECASE):
            temp_final2 = "Intel"
        elif re.match(r'American Megatrends', tempa2, re.IGNORECASE):
            temp_final2 = "AMI?"
        elif re.match(r'Phoenix Technologies', tempa2, re.IGNORECASE):
            temp_final2 = "Phoenix"
        else:
            temp_final2 = tempa2
        return temp_final2

    def lshw(self, fxml=""):
        """ Runs lshw and sets self.lshwxml variable if not already set """
        if not self.lshwxml:
            if fxml:
                f = open(fxml)
                self.lshwxml = f.read()
                f.close()
                print("\n\nUsing lshw xml file: %s" % fxml)
            else:
                # BUG: Wrong memory size with sudo? http://tinyurl.com/28q2elq
                self.lshwxml = self.runcommand(["sudo", "lshw", "-xml" , "-sanitize", "-numeric"])
            # Fix bug: https://bugs.launchpad.net/bugs/512251
            lines = self.lshwxml.split("\n")
            for l in lines:
                if re.search(r'id="lastmountpoint"', l):
                    lines.remove(l)
            self.lshwxml = '\n'.join(lines)
        doc = xml.dom.minidom.parseString(self.lshwxml)
        nodes = doc.getElementsByTagName("node")
        found_motherboard = False # Use alternative motherboard recognition data
        for n in nodes:
            if n.hasAttribute("class") and \
                n.getAttribute("class") == "system" and \
                n.hasAttribute("handle") and n.getAttribute("handle") == "DMI:0001":
                #<product>MS-7235</product><vendor>MICRO-STAR INTERNATIONAL CO.,LTD</vendor>
                #product: G31M-S2L - vendor: Gigabyte Technology Co., Ltd.
                tempa1 = n.getElementsByTagName("product")[0].childNodes[0].nodeValue
                tempa2 = n.getElementsByTagName("vendor")[0].childNodes[0].nodeValue
                temp_final2 = self.shortenmoboid(tempa2)
                if temp_final2 != "To Be Filled By O.E.M." and temp_final2 != "System manufacturer":
                    found_motherboard = True
                else:
                    # Clear default motherboard values
                    temp_final2 = ""
                    tempa1 = ""
                if not temp_final2:
                    self.lshwinfo["system"] = self.unknown
                else:
                    self.lshwinfo["system"] = "%s %s" % (temp_final2, tempa1)
                #print("MOO: %s %s" % (tempa1, tempa2))
            
            if n.hasAttribute("id"):

                if n.getAttribute("id") == "core":
                    #<product>MS-7235</product><vendor>MICRO-STAR INTERNATIONAL CO.,LTD</vendor>
                    #product: G31M-S2L - vendor: Gigabyte Technology Co., Ltd.
                    tempa1 = n.getElementsByTagName("product")[0].childNodes[0].nodeValue
                    tempa2 = n.getElementsByTagName("vendor")[0].childNodes[0].nodeValue
                    temp_final2 = self.shortenmoboid(tempa2)
                    if temp_final2 != "To Be Filled By O.E.M." and temp_final2 != "System manufacturer":
                        found_motherboard = True
                    else:
                        # Clear default motherboard values
                        temp_final2 = ""
                        tempa1 = ""
                    if not temp_final2:
                        self.lshwinfo["core"] = self.unknown
                    else:
                        self.lshwinfo["core"] = "%s %s" % (temp_final2, tempa1)
                    #print("MOO: %s %s" % (tempa1, tempa2))

                elif re.match(r'cpu(?::\n)?', n.getAttribute("id")):
                    try:
                        tempa = n.getElementsByTagName("product")[0].childNodes[0].nodeValue
                        if tempa[0:5] == "Intel" or tempa[0:7] == "Pentium": # Intel(R) Core(TM)2 Duo CPU     E6550  @ 2.33GHz
                            tempb = re.sub(r'\((?:R|TM)\)|CPU|@', ' ', tempa)
                            temp_final = re.sub('\s{2,}', ' ' , tempb)
                        elif tempa[0:3] == "AMD": # AMD Sempron(tm) Processor LE-1250, AMD Phenom(tm) II X2 550 Processor
                            tempb = re.sub(r'(?i)\((?:r|tm)\)|Processor', ' ', tempa)
                            temp_final = re.sub(r'\s{2,}', ' ' , tempb)
                        else:
                            temp_final = tempa
                        self.lshwinfo["cpu"] = temp_final
                    except IndexError:
                        pass

                elif re.match(r'display(?::\n)?', n.getAttribute("id")):
                    identified = False
                    try:
                        tempa1 = n.getElementsByTagName("product")[0].childNodes[0].nodeValue
                        # G73 [GeForce 7300 GT], Radeon R350 [Radeon 9800 Pro]
                        tempa2 = n.getElementsByTagName("vendor")[0].childNodes[0].nodeValue
                        # nVidia Corporation, ATI Technologies Inc
                        identified = True
                    except IndexError:
                        pass

                    if identified:
                        temp_final2 = tempa2
                        try:
                            if tempa2[0:6] == "nVidia":
                                temp_final2 = "nVidia"
                            elif tempa2[0:3] == "ATI":
                                temp_final2 = "ATI"
                            elif tempa2[0:5] == "Intel":
                                temp_final2 = "Intel"
                        except IndexError:
                            pass

                        displaystr = "%s %s" % (temp_final2, tempa1)
                        # Remove default data
                        try:
                            self.lshwinfo["display"].remove(self.unknown)
                        except ValueError:
                            pass
                        # Create an array with displays
                        try:
                            self.lshwinfo["display"].index(displaystr)
                        except ValueError:
                            self.lshwinfo["display"].append(displaystr)

                elif re.match(r'network(?::\n)?', n.getAttribute("id")):
                    identified = False
                    try:
                        tempdesc = n.getElementsByTagName("description")[0].childNodes[0].nodeValue
                        # Wireless interface, Ethernet interface
                        tempa1 = n.getElementsByTagName("product")[0].childNodes[0].nodeValue
                        # PRO/Wireless 2200BG [Calexico2] Network Connection, L1 Gigabit Ethernet Adapter
                        tempa2 = n.getElementsByTagName("vendor")[0].childNodes[0].nodeValue
                        # Realtek Semiconductor Co., Ltd., Intel Corporation, Atheros Communications
                        identified = True
                    except IndexError:
                        pass

                    if identified:
                        temptype = re.sub(r' interface', '', tempdesc)

                        temp_final2 = tempa2
                        try:
                            if tempa2[0:6] == "nVidia":
                                temp_final2 = "nVidia"
                            elif tempa2[0:3] == "VIA":
                                temp_final2 = "VIA"
                            elif tempa2[0:7] == "Atheros":
                                temp_final2 = "Atheros"
                            elif tempa2[0:5] == "Intel":
                                temp_final2 = "Intel"
                            elif tempa2[0:7] == "Realtek":
                                temp_final2 = "Realtek"
                            elif tempa2[0:8] == "Broadcom":
                                temp_final2 = "Broadcom"
                        except IndexError:
                            pass

                        networkstr = "%s: %s %s" % (temptype, temp_final2, tempa1)
                        # Remove default data
                        try:
                            self.lshwinfo["network"].remove(self.unknown)
                        except ValueError:
                            pass
                        # Create an array with networks
                        try:
                            self.lshwinfo["network"].index(networkstr)
                        except ValueError:
                            self.lshwinfo["network"].append(networkstr)

                elif re.match(r'memory(?::\n)?', n.getAttribute("id")):
                    try:
                        x = n.getElementsByTagName("description")[0].childNodes[0].nodeValue
                        if x == "System Memory":
                            tempa = n.getElementsByTagName("size")[0].childNodes[0].nodeValue
                            temp_final = int(tempa) / 1024**2 # Size in bytes, divide by 1024**2, result in MiB
                            self.lshwinfo["memory"] = temp_final
                    except IndexError:
                        pass

    def runcommand(self, command):
        p = subprocess.Popen(command, stdout=subprocess.PIPE)
        output = p.communicate()[0]
        return output

    def getfile(self, filename):
        f = open(filename, "r")
        lines = list(f.readlines())
        f.close()
        return lines


def main():
    #Argument: lshw xml filename (for testing)
    try:
        arg = sys.argv[1]
    except IndexError:
        arg = ""
    core(fxml=arg)

if __name__ == "__main__":
    main()

