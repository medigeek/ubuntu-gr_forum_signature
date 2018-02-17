#!/usr/bin/python
# -*- coding: utf-8 -*-
# File: forum_signature.py
# Purpose: Proposes a signature with useful hardware/software information to forum newcomers/newbies
# Requires: python 2.7, python-mechanize

# Copyright (c) 2010-2012 Savvas Radevic <vicedar@gmail.com>
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
1 Γνώσεις Linux: � ┃ Προγραμματισμού: � ┃ Αγγλικών: �
2 Ubuntu 11.04 natty 64bit (en_GB.utf8), Ubuntu 2.6.38-10-generic, Windows 7
3 Intel Core2 Duo CPU E6550 2.33GHz ‖ RAM 3961 MiB ‖ MSI MS-7235
4 nVidia G73 [GeForce 7300 GT] [10de:0393] (rev a1)
5 eth0: Realtek RTL-8110SC/8169SC Gigabit Ethernet [10ec:8167] (rev 10) ⋮ eth1: Realtek RTL-8139/8139C/8139C+ [10ec:8139] (rev 10)
"""

import platform
pyversion = platform.python_version()
if pyversion < '2.7':
    exit('ERROR: You need python 2.7 or higher to use this program.')
if platform.system() != "Linux":
    exit('ERROR: This script is built for GNU/Linux platforms (for now)')

import sys
import os
import os.path
import re
import subprocess
import time
import glob
import logging

import argparse
# PARSE ARGUMENTS
parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('-d', '--debug', action='store_true',
help='Debug (print out useful debug data)')
parser.add_argument('-t', '--text-only', action='store_true',
help='Print to console/terminal only')
args = parser.parse_args()
print(args)


# LOGS
log = logging.getLogger("forum-signature")
logfile = "forum-signature.log"
if os.path.isfile(logfile):
    os.remove(logfile)
formatter = logging.Formatter('%(levelname)s: %(message)s')
filehandler = logging.FileHandler(logfile)
filehandler.setFormatter(formatter)
streamhandler = logging.StreamHandler(sys.stdout)
streamhandler.setFormatter(formatter)
log.addHandler(filehandler)
log.addHandler(streamhandler)
if args.debug:
    log.setLevel(logging.DEBUG)
else:
    log.setLevel(logging.INFO)
log.debug("parsing arguments: {0}".format(args))
log.debug("osgrubber().returnall()")

try:
    from gi.repository import Gtk, Gdk
except (ImportError, RuntimeError):
    log.error("Could not load gtk+ 3 module. Setting text-only output.\n")
    args.text_only = True
try:
    from gi.repository import GObject
except ImportError:
    log.error("Could not load gobject module. Setting text-only output.\n")
    args.text_only = True

class core:
    def __init__(self, osgrubber, logger):
        self.osgrubbertuple = osgrubber
        self.log = logger
        self.pyversion = platform.python_version()
        self.unknown = "�" # Character/string for unknown data
        # Dictionary for dicreplace(), executed at returnall()
        self.dic = {
            "MICRO-STAR INTERNATIONAL CO.,LTD": "MSI",
            "MICRO-STAR INTERNATIONAL CO., LTD": "MSI",
            "Marvell Technology Group Ltd.": "Marvell",
            "Hewlett-Packard HP": "HP",
            "Broadcom Corporation": "Broadcom",
            "Silicon Integrated Systems [SiS]": "SiS",
            "Atheros Communications, Inc.": "Atheros",
            "Atheros Communications": "Atheros",
            "Atheros Inc.": "Atheros",
            "Acer, Inc.": "Acer",
            "ASUSTek Computer, Inc.": "ASUS",
            "ASUSTeK COMPUTER INC.": "ASUS",
            "ASUSTeK Computer": "ASUS",
            "Atheros Inc.": "Atheros",
            "ATI Technologies Inc": "ATI",
            "Gigabyte Technology Co., Ltd.": "Gigabyte",
            "VIA Technologies, Inc.": "VIA",
            "Intel Corporation": "Intel",
            "Apple Inc.": "Apple",
            "American Megatrends": "AMI?",
            "Phoenix Technologies": "Phoenix",
            "InnoTek": "Innotek",
            "Realtek Semiconductor Co., Ltd.": "Realtek",
            "Realtek Semiconductor Corp.": "Realtek",
            "nVidia Corporation": "nVidia",
            "ASUS INC.": "ASUS",
            "Ralink corp.": "Ralink",
            "Huawei Technologies Co., Ltd.": "Huawei",
            "NetGear, Inc.": "NetGear",
            "NVIDIA Corporation": "nVidia",
            "Accton Technology Corp.": "Accton",
            "Advanced Micro Devices [AMD] nee ATI": "AMD/ATI",
            "Advanced Micro Devices [AMD]": "AMD",
            "Integrated Graphics Controller": "Integrated Graphics",
            "PCI Express Fast Ethernet controller": "Ethernet",
            "Wireless LAN Controller": "Wireless",
            "http://www.": "",
            "abit.com.tw/": "",
            "(R)": "",
            "(TM)": "",
            "(r)": "",
            "(tm)": "",
            "  @ ": " ",
        }
        # Array for removing default motherboard vendor values
        self.defcoreid = [
            "System manufacturer",
            "System Product Name",
            "To Be Filled By O.E.M.",
        ]
        self.info = {
            "cpu": self.unknown,
            "memory": self.unknown,
            "display": list(self.unknown),
            "system": self.unknown,
            "core": self.unknown,
            "network": self.unknown,
        }
        self.lspci = ""
        self.lsusb = ""
        self.moduledrivers = dict()
        self.displaymanager = ""
        self.getlspci()
        self.getlsusb()
        self.getmoduledrivers()
        self.getdisplaymanager()
        self.getinfo()

    def printall(self):
        print(self.returnall())

    def returnall(self):
        x = self.knowledge()
        y = self.osinfo()
        z = self.specs()
        text = "{0}\n{1}\n{2}".format(x, y, z)
        t = self.dicreplace(text)
        return t

    def knowledge(self):
        s = {   "linux": self.unknown,
                "programming": self.unknown,
                "english": self.unknown
            }
        return "1 Γνώσεις Linux: {0} ┃ Προγραμματισμού: {1} ┃ Αγγλικών: {2}".format(
                s["linux"], s["programming"], s["english"])

    def osinfo(self):
        """ Returns OS info line (#2).
            Input: tuple list
            (osinfo, arch_type, iswubi, lang, self.oslist, self.osdict)
        """
        t = self.osgrubbertuple
        # is it wubi installation?
        if t[2]:
            wubi = "wubi"
        else:
            wubi = ""
        curroslist = [t[0], t[1], wubi]
        currosstr = ' '.join(curroslist).rstrip()
        lang = t[3]
        restofos = ', '.join(t[4])
        if restofos:
            s = "2 {0} ({1}, {2}), {3}".format(currosstr, lang, self.displaymanager, restofos)
        else:
            s = "2 {0} ({1}, {2})".format(currosstr, lang, self.displaymanager)
        #print(s)
        return s

    def specs(self):
        core = self.shortencoreid()
        text = '3 {0} ‖ RAM {1} MiB ‖ {2}\n4 {3}\n5 {4}'.format(
            self.info["cpu"],
            self.info["memory"],
            core,
            self.info["display"],
            self.info["network"]
        )
        return text

    def choosesudo(self):
        x = os.getenv('DESKTOP_SESSION', None)
        if x:
            if x == "gnome":
                return "gksu"
            if x == "kde" or x == "kde4":
                return "kdesudo"
            else: #Unknown sudo for other desktop managers
                return "sudo"
        else:
            return "sudo" # console session

    def shortencoreid(self):
        # Shorten the machine/motherboard id and manufacturer
        u = self.unknown # "�"
        u2 = "{0} {0}".format(u) # "� �"
        c = self.info["core"]
        if c[0] == c[1]:
            s = c[0]
        elif c[0] in (u,u2) and not c[1] in (u,u2):
            s = c[1]
        elif not c[0] in (u,u2) and c[1] in (u,u2):
            s = c[0]
        else:
            s = " - ".join(c)
        return s

    def getinfo(self):
        self.info["memory"] = self.getmeminfo()
        self.info["cpu"] = self.getcpuinfo()
        self.info["display"] = self.getdisplayinfo()
        self.info["network"] = self.getnetworkinfo()
        self.info["core"] = self.getcoreinfo() # Note: array

    def getcoreinfo(self):
        # Trying different files for motherboard chip identification
        f = {
            "board_vendor": "/sys/devices/virtual/dmi/id/board_vendor",
            "board_name": "/sys/devices/virtual/dmi/id/board_name",
            "sys_vendor": "/sys/devices/virtual/dmi/id/sys_vendor",
            "product_name": "/sys/devices/virtual/dmi/id/product_name",
        }
        # Read files and strip whitespace
        try:
            self.coreid = {
                "board_vendor": self.getfile(f["board_vendor"]).strip(),
                "board_name": self.getfile(f["board_name"]).strip(),
                "sys_vendor": self.getfile(f["sys_vendor"]).strip(),
                "product_name": self.getfile(f["product_name"]).strip(),
            }
            # Testing deldefcoreid()
            #self.coreid["board_vendor"] = "ASUS INC."
            #self.coreid["board_name"] = "P5Q"
            #self.coreid["sys_vendor"] = "System manufacturer"
            #self.coreid["product_name"] = "P5Q"
            # Drop default motherboard id values
            self.deldefcoreid()
        except IOError:
            # If files are not found
            t = [self.unknown, self.unknown]
            return t
        # Return an array of two strings
        t = [
            "{0} {1}".format(self.coreid["board_vendor"], self.coreid["board_name"]),
            "{0} {1}".format(self.coreid["sys_vendor"], self.coreid["product_name"])
        ]
        return t

    def deldefcoreid(self):
        # Deletes default motherboard id, matches self.defcoreid array
        # self.coreid = dictionary from getcoreinfo()
        c = self.coreid
        for x in c.keys():
            for d in self.defcoreid:
                if c[x] == d:
                    # If value in key matches default, clear it
                    self.coreid[x] = self.unknown

    def dicreplace(self, text):
        # self.dic is already prepared
        # METHOD 1
        #rx = re.compile('|'.join(map(re.escape, dic)))
        #def repl(m):
            #return dic[m.group(0)]
        #nt = rx.sub(repl, text)
        #return nt
        # METHOD 2
        # string.replace will get worse times as dictionary gets bigger
        s = text
        for key,val in list(self.dic.items()):
            ns = s.replace(key, val)
            s = ns
        s = re.sub("[ ]+", " ", s) #clear double or triple spaces
        return s

    def getlspci(self):
        if not self.lspci:
            p = ["lspci", "-nn"]
            self.lspci = self.runcommand(p)
    
    def getmoduledrivers(self):
        if not self.moduledrivers:
            #Alternative: Try using lspci -mm or -vmm or -m, e.g. lspci -vmm -v -nn -d 10de:0393
            files = glob.glob("/sys/bus/pci/devices/*/uevent")
            for f in files:
                s = self.getfile(f)
                m = re.search("DRIVER=(?P<driver>[^\n]*).*?PCI_ID=(?P<pci_id>[^\n]*)", s, re.S)
                if m:
                    d = m.groupdict()
                    self.moduledrivers[d["pci_id"]] = d["driver"]

    def getlsusb(self):
        if not self.lsusb:
            u = ["lsusb"]
            self.lsusb = self.runcommand(u)

    def getnetworkinfo(self):
        files = glob.glob("/sys/class/net/*/device/modalias")
        #netcards = dict()
        netcards = list()
        for f in files:
            name = f.split("/")[4] # ['', 'sys', 'class', 'net', 'eth1', 'device', 'modalias'
            s = self.getfile(f).strip()
            # PCI: v*d*s => [('10EC', '8139')]
            pciids = re.findall("v0000([0-9A-Z]+)d0000([0-9A-Z]+)s", s)
            #USB: v*p*d => [('0CF3', '1002')]
            usbids = re.findall("v([0-9A-Z]+)p([0-9A-Z]+)d", s)
            append = netcards.append # PythonSpeed/PerformanceTips
            if pciids:
                #04:01.0 Ethernet controller [0200]: Realtek Semiconductor Co., Ltd. RTL-8139/8139C/8139C+ [10ec:8139] (rev 10)
                mp = ":\s(.*{0}:{1}.*)".format(pciids[0][0], pciids[0][1])
                pcidesc = re.findall(mp, self.lspci, re.M+re.I)
                if pcidesc:
                    append("{0}: {1}".format(name, pcidesc[0]))
            if usbids:
                #Bus 002 Device 004: ID 0cf3:1002 Atheros Communications, Inc. TP-Link TL-WN821N v2 [Atheros AR9001U-(2)NG]
                mu = ":\sID\s({0}:{1}.*)".format(usbids[0][0], usbids[0][1])
                usbdesc = re.findall(mu, self.lsusb, re.M+re.I)
                append("{0}: {1}".format(name, usbdesc[0]))
        network = ' ⋮ '.join(netcards)
        return network

    def getdisplaymanager(self):
        l = list()
        for env in ['XDG_CURRENT_DESKTOP', 'DESKTOP_SESSION', 'GDMSESSION']:
            try:
                e = os.environ[env]
                if not e in l:
                    l.append(e)
            except KeyError:
                pass
        #print(" ".join(l))
        if l:
            self.displaymanager = " ".join(l)
        else:
            self.displaymanager = self.unknown
        #exit()

    def getdisplayinfo(self):
        l = list()
        m = re.compile("(?:VGA|3D)[^:]+:\s+(.+?)\s+\[(\w+:\w+)\]", re.M)
        displays = m.findall(self.lspci)
        #01:00.0 VGA compatible controller [0300]: NVIDIA Corporation G73 [GeForce 7300 GT] [10de:0393] (rev a1)
        #[('01:00.0 VGA compatible controller [0300]: NVIDIA Corporation G73 [GeForce 7300 GT] ', '[10de:0393]')]
        for (text, ident) in displays:
            try:
                mod = self.moduledrivers[ident.upper()]
            except KeyError:
                mod = '' # If no module is found
            l.append(text + " [" + ident + "] {" + mod + "}")
        graphics = ' ⋮ '.join(l)
        return graphics

    def getcpuinfo(self):
        f = "/proc/cpuinfo"
        s = self.getfile(f)
        # Processor model name
        match = re.search("model name\s+:\s+(.+)", s)
        x = match.group(1)
        # TODO: http://goo.gl/4k90P
        ## Number of cpu cores
        #match2 = re.search("cpu cores\s+:\s+(.+)", s)
        #z = match2.group(1)
        #cpu = "%sx %s" % (z, x)
        cpu = x
        return cpu

    def getmeminfo(self):
        f = "/proc/meminfo"
        s = self.getfile(f)
        match = re.search("MemTotal:\s+(\d+)", s, re.M)
        x = int(match.group(1)) # kilobytes, convert string to int
        memory = int(x / 1024) # megabytes
        return memory

    def getfile(self, filename, mode="string"):
        # Return file contents as a single string (string) or array list (list)
        # Default: string
        f = open(filename, "r")
        a = list(f.readlines())
        if mode == "string":
            lines = ''.join(a)
        elif mode == "list":
            lines = a
        f.close()
        return lines

    def runcommand(self, command):
        # python3 compatibility issue
        if self.pyversion >= '3.0.0':
            c = command
            if type(command) == type(list()):
                c = ' '.join(command)
            output = subprocess.getoutput(c)
        else:
            p = subprocess.Popen(command, stdout=subprocess.PIPE)
            output = p.communicate()[0]
        return output

class siggui:
    """ The graphical user interface for timekpr configuration. """
    def __init__(self, text, osgrubber, logger, debug=False):
        self.debug = debug
        #osgrubber: (osinfo, arch_type, iswubi, lang, self.oslist, self.osdict, self.morethan2)
        self.is_wubi = osgrubber[2]
        self.more_than_two = osgrubber[6]
        self.log = logger
        self.unknown = "�"
        self.username = ""
        self.password = ""
        self.sig_charlimit = 600 # Allowed number of characters
        # UI FILE
        self.uifile = "forum_signature_gtk3.glade"
        self.builder = Gtk.Builder()
        self.builder.add_from_file(self.uifile)
        #SIGNALS
        self.builder.connect_signals(self)
        # WINDOW
        self.window = self.builder.get_object("window1")
        self.textbox_label = self.builder.get_object("label5") 
        self.textbox = self.builder.get_object("textview1") # new/pending sig
        self.textboxbuf = self.textbox.get_buffer()
        self.textboxbuf.connect("changed", self.on_textboxbuf_changed)
        self.textboxbuf.set_text(text)
        self.textbox2 = self.builder.get_object("textview2") # old sig
        self.textboxbuf2 = self.textbox2.get_buffer()
        
        self.liststore = self.builder.get_object("liststorecombo1")
        self.comboboxlinux = self.builder.get_object("comboboxtext1")
        self.comboboxlinux.set_model(self.liststore)
        self.comboboxprogramming = self.builder.get_object("comboboxtext2")
        self.comboboxprogramming.set_model(self.liststore)
        self.comboboxenglish = self.builder.get_object("comboboxtext3")
        self.comboboxenglish.set_model(self.liststore)
        
        self.statusbar = self.builder.get_object("statusbar1")
        self.statusbarcid = self.statusbar.get_context_id("status")
        self.oldsigpack = self.builder.get_object("expander1")
        # DIALOG
        self.dialog = self.builder.get_object("dialog1")
        self.dialog.set_default_response(Gtk.ResponseType.CANCEL)
        self.entry1 = self.builder.get_object("entry1")
        self.entry2 = self.builder.get_object("entry2")
        # BUG REPORT DIALOG
        self.reportbugdialog = self.builder.get_object("reportbug")
        self.textboxbuf3 = self.builder.get_object("textview3")
        # ERROR MESSAGE DIALOG
        self.errormsg = self.builder.get_object("messagedialog1")
        # Ubuntu Hardy 8.04 compatibility
        self.comboboxlinux.set_entry_text_column(0)
        self.comboboxprogramming.set_entry_text_column(0)
        self.comboboxenglish.set_entry_text_column(0)
        # CHECK WUBI
        self.iswubi()
        # CHECK if has more than 2 OS on same device partition
        self.hasmorethan2()

    def on_textboxbuf_changed(self, widget):
        (start, end) = self.textboxbuf.get_bounds()
        sigtext = self.textboxbuf.get_text(start, end, include_hidden_chars=False)
        self.sig_size = len(sigtext)
        # Could use this to drop code tags: re.sub(r'\[([^\s]*).*?\](.*?)\[/\1\]', r'\2', text)
        if self.sig_size > self.sig_charlimit:
            l = "Υπογραφή: Χαρακτήρες: <span foreground='red'>{0}</span> \
(Επιτρέπονται μέχρι {1} χαρακτήρες)"
        else:
            l = "Υπογραφή: Χαρακτήρες: {0} (Επιτρέπονται μέχρι {1} χαρακτήρες)"
        self.textbox_label.set_markup(l.format(self.sig_size, self.sig_charlimit))

    def on_button7_clicked(self, widget):
        self.reportbug()

    def reportbug(self):
        p = subprocess.Popen(["cat", "/proc/cpuinfo"], stdout=subprocess.PIPE)
        outcpu = p.communicate()[0]

        p = subprocess.Popen(["cat", "/proc/meminfo"], stdout=subprocess.PIPE)
        outmem = p.communicate()[0]

        p = subprocess.Popen(["lspci", "-nn"], stdout=subprocess.PIPE)
        outlspci = p.communicate()[0]

        p = subprocess.Popen("lsusb", stdout=subprocess.PIPE)
        outlsusb = p.communicate()[0]

        (start, end) = self.textboxbuf.get_bounds()
        sigtext = self.textboxbuf.get_text(start, end, include_hidden_chars=False)

        text = "Περιγράψτε το πρόβλημα στη θέση αυτού του κειμένου.\n\
Επισυνάψτε σφάλμα από το τερματικό ή από το γραφικό περιβάλλον (αν υπάρχει).\n\n\
------------------------\n\
Πληροφορίες:[code]\n\
* cpuinfo\n{0}\n\
* meminfo:\n{1}\n\
* lspci:\n{2}\n\
* lsusb:\n{3}\n\
* signature:\n{4}\n\
[/code]".format(outcpu, outmem, outlspci, outlsusb, sigtext)

        # SAVE TO CLIPBOARD
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(text, -1)
        clipboard.store()

        buf = self.textboxbuf3.get_buffer()
        buf.set_text(text)
        dialogreply = self.reportbugdialog.run()
        #print("%s %s" % (type(dialogreply), dialogreply))
        self.reportbugdialog.hide()

    def hasmorethan2(self):
        # Check if more than two OS present in system.
        if self.more_than_two:
            mt2 = ' '.join(self.more_than_two)
            s = "<b>ΕΝΗΜΕΡΩΣΗ</b>: Περισσότερα από 2 Λειτουργικά Συστήματα"
            s2 = 'Έχετε περισσότερες από 2 εκδόσεις πυρήνα (kernel) εγκατεστημένες \
στην ίδια κατάτμηση: {0}\n\
<a href="https://forum.ubuntu-gr.org/viewtopic.php?f=9&t=31328">Διαβάστε \
εδώ</a> για περισσότερες πληροφορίες και για οδηγίες αφαίρεσης των επιπλέον πυρήνων.'.format(mt2)
            self.messagedialog(s, s2)

    def iswubi(self):
        # Check if its wubi
        if self.is_wubi:
            s = "<b>ΠΡΟΕΙΔΟΠΟΙΗΣΗ</b>: Δε συστήνεται η εγκατάσταση μέσω wubi."
            s2 = "Η εγκατάσταση που έχετε έγινε μέσω <span foreground='red'>wubi</span>. \
Τετοια εγκατάσταση συστήνεται μόνο για δοκιμαστικούς σκοπούς \
(<a href='http://wiki.ubuntu-gr.org/whynotwubi'>διαβάστε τους λόγους</a>).\n\
Διαβάστε στους <a href='http://forum.ubuntu-gr.org/viewtopic.php?f=9&amp;t=859'>\
οδηγούς/how to/tutorials</a> πώς να κάνετε σωστή εγκατάσταση."
            self.messagedialog(s, s2)

    def statusmsg(self, message):
        msg = "{0} {1}".format(time.strftime("%Y-%m-%d %H:%M:%S"), message)
        msgid = self.statusbar.push(self.statusbarcid, msg)
        #self.statusrefresh()
        timeoutid2 = GObject.timeout_add_seconds(4, self.statusrefresh, msgid)

    def statusrefresh(self, msgid):
        self.statusbar.remove(self.statusbarcid, msgid)
    
    def gtk_main_quit(self, widget):
        Gtk.main_quit()

    def on_comboboxentry_changed(self, widget):
        linux = self.comboboxlinux.get_active_text()
        programming = self.comboboxprogramming.get_active_text()
        english = self.comboboxenglish.get_active_text()
        self.line = "Γνώσεις Linux: {0} ┃ Προγραμματισμού: {1} ┃ Αγγλικών: {2}".format(
            linux, programming, english)
        (start, end) = self.textboxbuf.get_bounds()
        oldtext = self.textboxbuf.get_text(start, end, include_hidden_chars=False) # get all text
        newtext = re.subn(
            'Γνώσεις Linux:.*┃ Προγραμματισμού:.*┃ Αγγλικών:.*',
            self.line,
            oldtext
        ) # newtext is a touple ("newstring", times_of_substitution)
        if newtext[1] > 0: # If substitutions took place
            self.textboxbuf.set_text(newtext[0])
        else: # If no substitutions took place
            if oldtext == "":
                self.textboxbuf.set_text(self.line)
            else:
                self.textboxbuf.set_text("{0}\n{1}".format(oldtext, self.line))

    def checksigsize(self):
        if self.sig_size > self.sig_charlimit:
            errormsg1 = 'Ξεπεράσατε το επιτρεπόμενο όριο χαρακτήρων!'
            errormsg2 = 'Επιτρέπονται μέχρι 500 χαρακτήρες. Αλλάξτε την \
υπογραφή σας. Αν θέλετε να χρησιμοποιήσετε code tags, ακολουθήστε \
<a href="http://forum.ubuntu-gr.org/ucp.php?i=profile&amp;mode=signature">αυτό \
το σύνδεσμο</a> και υποβάλετε την υπογραφή μέσω της ιστοσελίδας.'
            self.messagedialog("<b>ΣΦΑΛΜΑ</b>: {0}".format(errormsg1), errormsg2)
            return True
        return False

    def on_button1_clicked(self, widget):
        # Check size
        if not self.checksigsize():
            # Submit to forum
            dialogreply = self.dialog.run()
            if dialogreply == Gtk.ResponseType.APPLY:
                self.statusmsg("Επικοινωνία...")
                timeid = GObject.timeout_add_seconds(1, self.webwrapper)
            self.dialog.hide()

    def webwrapper(self):
        webreply = self.sendtoweb()
        #oldsig = "oldsig test"
        if webreply[0] == 0:
            self.textboxbuf2.set_text(webreply[1])
            self.oldsigpack.set_expanded(True)
        else:
            pass

    def gtk_false(self, *widget):
        # DIALOG - Cancel
        self.dialog.response(Gtk.ResponseType.CANCEL)

    def gtk_true(self, *widget):
        # DIALOG - Continue
        self.dialog.response(Gtk.ResponseType.APPLY)

    def on_entry1_changed(self, widget):
        # DIALOG - Username
        self.username = self.entry1.get_text()

    def on_entry2_changed(self, widget):
        # DIALOG - Password
        self.password = self.entry2.get_text()

    def messagedialog(self, msg1, msg2):
        self.errormsg.set_markup(msg1)
        self.errormsg.format_secondary_markup(msg2)
        dialogreply = self.errormsg.run()
        self.errormsg.hide()

    def sendtoweb(self):
        (start, end) = self.textboxbuf.get_bounds()
        text = self.textboxbuf.get_text(start, end, include_hidden_chars=False)

        try:
            m = __import__("mechanize")
        except ImportError:
            errormsg1 = "<b>ΣΦΑΛΜΑ</b>: Δεν έχετε εγκατεστημένο το python-mechanize."
            errormsg2 = 'Για να αποσταλεί η υπογραφή σας πρέπει να εγκαταστήσετε \
το πακέτο/πρόγραμμα python-mechanize. Αλλιώς ακολουθήστε \
<a href="http://forum.ubuntu-gr.org/ucp.php?i=profile&amp;mode=signature">αυτό \
το σύνδεσμο</a> και υποβάλετε την υπογραφή μέσω της ιστοσελίδας.'
            self.messagedialog(errormsg1, errormsg2)
            return (1, errormsg1)
        br = m.Browser()
        #('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:2.0.1) Gecko/20100101 Firefox/4.0.1'),
        br.addheaders = [
            ('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.7'),
            ('Accept-Language', 'Accept-Language: en-us,en;q=0.7,el;q=0.3'),
            ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
        ]
        #br.set_handle_redirect(True)
        #br.set_handle_equiv(True)
        #br.set_handle_gzip(True)
        br.set_handle_referer(True)
        br.set_handle_robots(False)
        br.set_handle_refresh(m._http.HTTPRefreshProcessor(), max_time=1)

        # Debug!
        if self.debug:
            br.set_debug_http(True)
            br.set_debug_redirects(True)
            br.set_debug_responses(True)
            logger = logging.getLogger("mechanize")
            #logger.addHandler(logging.StreamHandler(sys.stdout))
            logger.addHandler(logging.FileHandler("http.log"))
            logger.setLevel(logging.DEBUG)

        br.open("http://forum.ubuntu-gr.org/ucp.php?i=profile&mode=signature")
        #self.statusmsg("Logging in...")
        br.select_form(nr=1) # Select login form (no name for the form)
        br["username"] = self.username
        br["password"] = self.password
        r1 = br.submit()
        h1 = r1.read()

        m = re.search('<div class="error">(.*)</div>', h1)
        if m:
            errormsg = m.group(1)
            if re.search("Έχετε υπερβεί το μέγιστο αριθμό προσπαθειών σύνδεσης", errormsg):
                errormsg1 = 'Έχετε υπερβεί το μέγιστο αριθμό προσπαθειών σύνδεσης.'
                errormsg2 = 'Εκτός από το όνομα μέλους και τον κωδικό πρόσβασης σας \
τώρα επίσης πρέπει να εισαγάγετε και τον κώδικα επιβεβαίωσης. Για να συνεχίσετε \
να χρησιμοποιείτε το πρόγραμμα, πρέπει να κάνετε login/σύνδεση στην ιστοσελίδα \
του φόρουμ, <a href="http://forum.ubuntu-gr.org">http://forum.ubuntu-gr.org</a>'
                self.messagedialog("<b>ΣΦΑΛΜΑ</b>: {0}".format(errormsg1), errormsg2)
            else:
                self.messagedialog("<b>ΣΦΑΛΜΑ</b>: {0}".format(errormsg), "")
            self.statusmsg("Σφάλμα: {0}".format(errormsg))
            return (1,"Σφάλμα: {0}".format(errormsg))

        r2 = br.follow_link(url_regex='.*profile.*mode=signature.*sid')
        br.select_form(nr=1)
        oldsig = br["signature"]
        br["signature"] = text

        r3 = br.submit(name='submit')
        h3 = r3.read()
        m = re.search('<p class="error">(.*)</p>', h3)
        if m:
            errormsg = m.group(1)
            if re.search("Η υποβληθείσα μορφή ήταν άκυρη", errormsg):
                errormsg1 = 'Η υποβληθείσα μορφή ήταν άκυρη'
                errormsg2 = 'Προσπαθήστε πάλι. Σε περίπτωση που επαναληφθεί, ακολουθήστε \
<a href="http://forum.ubuntu-gr.org/ucp.php?i=profile&amp;mode=signature">αυτό \
το σύνδεσμο</a> και υποβάλετε την υπογραφή μέσω της ιστοσελίδας.'
                self.messagedialog("<b>ΣΦΑΛΜΑ</b>: {0}".format(errormsg1), errormsg2)
            else:
                self.messagedialog("<b>ΣΦΑΛΜΑ</b>: {0}".format(errormsg), "")
            self.statusmsg("Σφάλμα: {0}".format(errormsg))
            return (1,"Σφάλμα: {0}".format(errormsg))

        r4 = br.follow_link(url_regex='ucp\.php.*mode=logout')

        self.statusmsg("Υποβλήθηκε στο φόρουμ!")
        return (0,oldsig)

class osgrubber:
    """ Retrieves information about installed operating systems. """
    def __init__(self, logger):
        self.oslist = list()
        self.osdict = dict()
        self.log = logger
        self.result = ""
        self.morethan2 = set() #python2.6 or: from sets import Set as set
        self.read_grub() # Sets self.oslist array
        self.finalize()

    def printall(self):
        import pprint
        pprint.pprint(self.result)

    def returnall(self):
        return self.result

    def finalize(self):
        """ Finalizes the processing.
            Returns a tuple list:
            (osinfo, arch_type, iswubi, lang, self.oslist, self.osdict, self.morethan2)
        """
        iswubi = self.is_wubi()
        if self.is_wubi():
            wubi = "wubi"
        else:
            wubi = ""

        arch_type = self.machinearch()
        osinfo = self.osinfo()
        lang = self.oslang()
        self.result = (osinfo, arch_type, iswubi, lang, self.oslist, self.osdict, self.morethan2)

    def osinfo(self):
        # Returns current OS info string
        # Return example: 'Ubuntu 12.04 precise 3.4.4-030404-generic'
        d = platform.linux_distribution()
        kernelver = platform.uname()[2]
        distrib = '{0} {1}'.format(' '.join(d), kernelver)
        return distrib

    def oslang(self):
        lang = os.getenv("LANG", "en_US") # Assume en_US if LANG var not set
        return lang

    def machinearch(self):
        m = platform.architecture()
        #('64bit', 'ELF')
        return m[0]

    def truncate_titles(self, t):
        """ Trucate title of OS in read_grub() """
        s = re.sub(',? [^\s]*? Linux.*', '', t)
        s = re.sub('\([^\)]*?\)$|\s*?\(loader\)', '', s)
        s = re.sub('\s+', ' ', s).rstrip()
        self.log.debug("Trimmed OS title: '{0}'".format(s))
        return s

    def read_grub(self):
        """ Retrieves operating systems from grub configuration file.
            Sets self.oslist list (max 2 OS per partition)
            Sets self.osdict dictionary (all OS, categorised by device)
            Populates self.morethan2 if more than 2 OS found on same partition
            Returns True/False
            
            self.osdict example:
            d['hd2,msdos1']
                [{'linuxstr': None, 'title': 'Windows 7 (on /dev/sdc1)'}]
            d['hd2,msdos1'][0]['title']
                'Windows 7 (on /dev/sdc1)'
        """
        #Does grub.cfg exist?
        grub2_fname = "/boot/grub/grub.cfg"
        if not os.path.isfile(grub2_fname):
            return False
        with open(grub2_fname) as f:
            grub2_cont = f.read()

        #Create empty dict with grub menuentry-ies
        dct = dict()
        li = list()
        regexstr = "menuentry ['\"](?P<title>.*?)['\"].*?set root='\(?(?P<device>.*?)\)?'(?:.*?(?:chainloader.*?\n|(?:linux16|linux)\s(?P<linuxstr>.*?)\n)|.*?)"

        for m in re.finditer(regexstr, grub2_cont, re.S):
            self.log.debug("*** Matched grub line: {0}".format(m.groups()))
            l = m.group('linuxstr')

            t = m.group('title')
            if not l == None and (t == "Ubuntu" or "Fallback" in t or "ανάκτηση" in t or "fallback" in l or "recovery" in l or "memtest" in l):
                #Ignore memtest and linux recovery grub menuentry-ies
                self.log.debug("Blacklisted, skipping this line")
                continue
            if "Recovery" in t:
                # Ignore windows recovery
                self.log.debug("Blacklisted, skipping this line")
                continue
            d = m.group('device')

            # Match version in linux string
            if not l == None:
                mre = re.match(".*vmlinuz-([^\s]*)", l)
                if mre:
                    v = mre.group(1)
                    self.log.debug("Found linux version: '{0}' from '{1}'".format(v, l))
                else:
                    v = ""
                    self.log.debug("Could not find linux version from '{0}'".format(l))
            else:
                v = ""
                self.log.debug("Could not find linux version from '{0}'".format(l))
            
            # Truncate titles
            tx = self.truncate_titles(t)
            ltv = " ".join([tx,v]).rstrip()
            self.log.debug("Concatenated title and version: '{0}'".format(ltv))
            
            if not dct.has_key(d):
                dct[d] = list()
            # Keep all the OS in the dictionary
            dct[d].append({'title': tx, 'linuxstr': l, 'version': v})
            # Do not save current OS in the list
            # Do not save more than two OS of the same partition in the list
            self.log.debug("Checks: append to OS list if not current OS & not more than 2 OS")
            if not self.is_currentos(ltv) and len(dct[d]) < 3:
                self.log.debug("Appending to OS list: '{0}' in device '{1}'".format(ltv, d))
                li.append(ltv)
            elif not len(dct[d]) < 3:
                self.log.debug("More than 2 OS found on device: {0} -- will not append '{1}' to OS list".format(d, ltv))
                self.morethan2.add(d)
            self.log.debug("Current OS list: {0}\nCurrent device {1} dict: {2}\nCurrent 'more than 2 kernels' list: {3}\n".format(li, d, dct[d], self.morethan2))

        self.oslist = li
        self.osdict = dct
        self.log.debug("Final OS list: {0}\nFinal OS dict: {1}\nFinal 'more than 2 kernels' list: {2}\n".format(self.oslist, self.osdict, self.morethan2))
        if self.morethan2:
            mt2 = ' '.join(self.morethan2)
            self.log.warning("More than 2 OS found on device(s): {0}".format(mt2))
        return True

    def is_currentos(self, osline):
        """ Detect current os (based on linux version) in self.oslist
            Returns True/False
        """
        un = platform.uname()
        #('Linux', 'home-desktop', '2.6.38-8-generic', '#42-Ubuntu SMP Mon Apr 11 03:31:24 UTC 2011', 'x86_64', 'x86_64')
        if not un[0] == "Linux":
            return False
        currlinver = un[2].replace('.', '\.') #escape dots (regex)
        if re.search(currlinver, osline):
            # If current linux version is found in a grub os line
            self.log.debug("Matches current OS: '{0}'".format(osline))
            return True
        return False

    def is_wubi(self):
        # Detects wubi installation
        # Scans /etc/fstab for loop devices as root "/" and swap
        #return True # Uncomment this for testing
        fstabfile = "/etc/fstab" # /etc/fstab
        if not os.path.isfile(fstabfile):
            return False
        with open(fstabfile, "r") as f:
            a = list(f.readlines())
        lines = ''.join(a)
        f.close()
        #print(lines)
        matches = re.findall("^([^#][^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)", lines, re.M)
        #Returns: [('proc', '/proc', 'proc', 'nodev,noexec,nosuid'),
        #('/host/ubuntu/disks/root.disk', '/', 'ext4', 'loop,errors=remount-ro'),
        #('/host/ubuntu/disks/swap.disk', 'none', 'swap', 'loop,sw')]

        # Wubi uses a feature called "loop device" to load its root/swap files.
        root_looped = False
        swap_looped = False
        for dev,mpoint,part,opts in matches:
            if mpoint == "/" and re.match("loop", opts):
                root_looped = True
            if part == "swap" and re.match("loop", opts):
                swap_looped = True
        if root_looped and swap_looped:
            self.log.warning("wubi installation detected.\n")
            return True
        else:
            return False

def main():
    global args, log
    o = osgrubber(logger=log).returnall()
    #(osinfo, arch_type, iswubi, lang, self.oslist, self.osdict, self.morethan2)
    log.debug("core(o).returnall()")
    text = core(o, logger=log).returnall()
    if args.text_only:
        log.debug("Console-only output")
        print(text)
    else:
        log.debug("Console and gui output")
        print(text)
        siggui(text, osgrubber=o, logger=log, debug=args.debug)
        Gtk.main()
    logging.shutdown()

def timeit():
    f = 'core(osgrubber().returnall()).returnall()'
    import cProfile
    cProfile.run(f)
    import timeit
    t = timeit.Timer(f, 'from __main__ import osgrubber, core')
    print(t.timeit(number=100))

if __name__ == "__main__":
    main()
    #timeit()
