#!/usr/bin/python
# -*- coding: utf-8 -*-
# File: ubuntu-gr_signature.py
# Purpose: Proposes a signature with useful hardware/software information to forum newcomers/newbies
# Requires: python 2.5, lshw, sudo (for motherboard chip recognition)

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

"""Example of signature:
Γνώσεις ⇛ Linux: Άγνωστο ┃ Προγραμματισμός: Άγνωστο ┃ Αγγλικά: Άγνωστο
Λειτουργικό: Ubuntu 10.10 64-bit (en_GB.utf8)
Προδιαγραφές ⇛ Intel Core 2 Duo E6550 2.33GHz │ RAM 2008 MiB │ nVidia G73 [GeForce 7300 GT]│ Μητρική: MSI MS-7235
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
    def __init__(self):
        # unicode("Πολύ καλές", "utf-8")
        self.lshwxml = ""
        self.lshwinfo = {}
        self.lshw()
        self.knowledge()
        self.osinfo()
        self.specs()

    def knowledge(self):
        s = {   "linux": u"Άγνωστο",
                "programming": u"Άγνωστο",
                "english": u"Άγνωστο"
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
            #elif lx[0] == "DISTRIB_CODENAME":
            #    distrib["code"] = lx[1].rstrip("\n")
            #elif lx[0] == "DISTRIB_DESCRIPTION":
            #    distrib["desc"] = lx[1].rstrip("\n")
        lang = self.oslang()
        arch_type = self.machinearch()
        print(u"Λειτουργικό: %s %s %s (%s)" % (distrib["id"], distrib["rel"],
            arch_type, lang))

    def oslang(self):
        #cat /etc/environment
        lines = self.getfile("/etc/environment")
        lang = "en_US"
        for l in lines:
            lx = l.split("=")
            if lx[0] == "LANG":
                lang = lx[1].strip('"\n')
        return lang

    def machinearch(self):
        output = os.uname()[4]
        if output == "x86_64":
            mtype = "64-bit"
        elif output == "x86":
            mtype = "32-bit"
        else:
            mtype = "x-bit"
        return mtype

    def specs(self):
        print( u'Προδιαγραφές ⇛ %s │ RAM %s MiB │ %s│ Μητρική: %s' %
                (self.lshwinfo["cpu"],
                self.lshwinfo["memory"],
                self.lshwinfo["display"],
                self.lshwinfo["system"])
        )

    def cpuinfo(self):
        print("CPU: %s" % self.lshwinfo["cpu"])

    def display(self):
        print("Display: %s" % self.lshwinfo["display"])

    def memory(self):
        print("Memory: %d MiB" % self.lshwinfo["memory"])

    def mainboard(self):
        print("Mainboard: %s" % self.lshwinfo["system"])

    def lshw(self):
        """ Runs lshw and sets self.lshwxml variable if not already set """
        if not self.lshwinfo:
            if not self.lshwxml:
                self.lshwxml = self.runcommand(["sudo", "lshw", "-xml"])
                # Fix bug: https://bugs.launchpad.net/bugs/512251
                lines = self.lshwxml.split("\n")
                for l in lines:
                    if re.search(r'id="lastmountpoint"', l):
                        lines.remove(l)
                self.lshwxml = '\n'.join(lines)
            doc = xml.dom.minidom.parseString(self.lshwxml)
            nodes = doc.getElementsByTagName("node")
            for n in nodes:
                if n.hasAttribute("class") and n.getAttribute("class") == "system":
                    #<product>MS-7235</product><vendor>MICRO-STAR INTERNATIONAL CO.,LTD</vendor>
                    #product: G31M-S2L - vendor: Gigabyte Technology Co., Ltd.
                    tempa1 = n.getElementsByTagName("product")[0].childNodes[0].nodeValue
                    tempa2 = n.getElementsByTagName("vendor")[0].childNodes[0].nodeValue
                    if re.match(r'MICRO-STAR INTERNATIONAL', tempa2, re.IGNORECASE):
                        temp_final2 = "MSI"
                    elif re.match(r'Gigabyte Technology Co\., Ltd\.', tempa2, re.IGNORECASE):
                        temp_final2 = "Gigabyte"
                    else:
                        temp_final2 = tempa2
                    self.lshwinfo["system"] = "%s %s" % (temp_final2, tempa1)
                    #print("MOO: %s %s" % (tempa1, tempa2))
                    
                if n.hasAttribute("id"):
                    if n.getAttribute("id") == "cpu":
                        tempa = n.getElementsByTagName("product")[0].childNodes[0].nodeValue
                        if tempa[0:5] == "Intel": # Intel(R) Core(TM)2 Duo CPU     E6550  @ 2.33GHz
                            tempb = re.sub(r'\((?:R|TM)\)|CPU|@', ' ', tempa)
                            temp_final = re.sub('\s{2,}', ' ' , tempb)
                        elif tempa[0:3] == "AMD": # AMD Sempron(tm) Processor LE-1250, AMD Phenom(tm) II X2 550 Processor
                            tempb = re.sub(r'(?i)\((?:r|tm)\)|Processor', ' ', tempa)
                            temp_final = re.sub(r'\s{2,}', ' ' , tempb)
                        else:
                            temp_final = tempa
                        self.lshwinfo["cpu"] = temp_final
                    elif n.getAttribute("id") == "display":
                        tempa1 = n.getElementsByTagName("product")[0].childNodes[0].nodeValue
                        # G73 [GeForce 7300 GT], Radeon R350 [Radeon 9800 Pro]
                        tempa2 = n.getElementsByTagName("vendor")[0].childNodes[0].nodeValue
                        # nVidia Corporation, ATI Technologies Inc
                        if tempa2[0:6] == "nVidia":
                            temp_final2 = re.sub(r'(?i)\sCorporation', '', tempa2)
                        elif tempa2[0:3] == "ATI":
                            temp_final2 = re.sub(r'(?i)\sTechnologies\sInc', '', tempa2)
                        else:
                            temp_final2 = tempa2
                        self.lshwinfo["display"] = "%s %s" % (temp_final2, tempa1)
                    elif n.getAttribute("id") == "memory":
                        tempa = n.getElementsByTagName("size")[0].childNodes[0].nodeValue
                        temp_final = int(tempa) / 1024**2 # Size in bytes, divide by 1024**2, result in MiB
                        self.lshwinfo["memory"] = temp_final

    def runcommand(self, command):
        p = subprocess.Popen(command, stdout=subprocess.PIPE)
        #p.stdout.readlines()
        #waitpid = os.waitpid(p.pid, 0)
        output = p.communicate()[0]
        return output

    def getfile(self, filename):
        f = open(filename, "r")
        lines = list(f.readlines())
        f.close()
        return lines

def main():
    #print("YO!")
    core()

if __name__ == "__main__":
    main()

