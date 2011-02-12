#!/usr/bin/python
# -*- coding: utf-8 -*-
# File: ubuntu-gr_signature.py
# Purpose: Proposes a signature with useful hardware/software information to forum newcomers/newbies
# Requires: python 2.5, python-gtk2, python-mechanize

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
import platform

if sys.version < '2.5':
    sys.exit('ERROR: You need python 2.5 or higher to use this program.')
if platform.system() != "Linux":
    sys.exit('ERROR: This script is built for GNU/Linux platforms (for now)')

import os

import re
import subprocess
import time
import string
import glob

import pygtk
pygtk.require('2.0')
import gtk
import glib

class core:
    def __init__(self):
        self.unknown = u"�" # Character/string for unknown data
        # Dictionary for dicreplace()
        self.dic = {
            "MICRO-STAR INTERNATIONAL CO.,LTD": "MSI",
            "Atheros Communications, Inc.": "Atheros",
            "Gigabyte Technology Co., Ltd.": "Gigabyte",
            "ASUSTeK Computer": "ASUS",
            "Intel Corporation": "Intel",
            "American Megatrends": "AMI?",
            "Phoenix Technologies": "Phoenix",
            "InnoTek": "Innotek",
            "Realtek Semiconductor Co., Ltd.": "Realtek",
            "nVidia Corporation": "nVidia",
            "(R)": "",
            "(TM)": "",
            "(r)": "",
            "(tm)": "",
            "     ": " ",
            "  @ ": " ",
        }
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
        self.getlspci()
        self.getlsusb()
        self.getinfo()

    def printall(self):
        print(self.returnall())

    def returnall(self):
        x = self.knowledge()
        y = self.osinfo()
        z = self.specs()
        text = u"%s\n%s\n%s" % (x, y, z)
        t = self.dicreplace(text)
        return t

    def knowledge(self):
        s = {   "linux": self.unknown,
                "programming": self.unknown,
                "english": self.unknown
            }
        return u"Γνώσεις ⇛ Linux: %s ┃ Προγραμματισμός: %s ┃ Αγγλικά: %s" % \
                (s["linux"], s["programming"], s["english"])

    def osinfo(self):
        # ('Ubuntu', '10.10', 'maverick')
        try:
            d = platform.linux_distribution()
        except AttributeError:
            d = platform.dist() # For python versions < 2.6
        distrib = ' '.join(d)
        lang = self.oslang()
        arch_type = self.machinearch()
        s = u"Λειτουργικό: %s %s (%s)" % (distrib, arch_type, lang)
        return s

    def specs(self):
        core = self.shortencoreid()
        text = u'Προδιαγραφές ⇛ %s │ RAM %s MiB │ %s\nΚάρτες γραφικών: %s\nΔίκτυα: %s' % \
            (self.info["cpu"],
            self.info["memory"],
            core,
            self.info["display"],
            self.info["network"]
        )
        return text

    def oslang(self):
        lang = os.getenv("LANG", "en_US") # Assume en_US if LANG var not set
        return lang  

    def machinearch(self):
        m = platform.machine()
        if m == "x86_64":
            mtype = "64-bit"
        elif m == "i386" or m == "i686":
            mtype = "32-bit"
        else:
            mtype = "%s-bit" % self.unknown
        return mtype

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
        if self.info["core"][0] == self.info["core"][1]:
            s = self.info["core"][0]
        elif self.info["core"][0] == self.unknown and not self.info["core"][1] == self.unknown:
            s = self.info["core"][1]
        elif not self.info["core"][0] == self.unknown and self.info["core"][1] == self.unknown:
            s = self.info["core"][0]
        else:
            s = " - ".join(self.info["core"])
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
            s = {
                "board_vendor": self.getfile(f["board_vendor"]).strip(),
                "board_name": self.getfile(f["board_name"]).strip(),
                "sys_vendor": self.getfile(f["sys_vendor"]).strip(),
                "product_name": self.getfile(f["product_name"]).strip(),
            }
        except IOError:
            # If files are not found
            t = [self.unknown, self.unknown]
            return t
        # Return an array of two strings
        t = [
            "%s %s" % (s["board_vendor"], s["board_name"]),
            "%s %s" % (s["sys_vendor"], s["product_name"])
        ]
        return t

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
        for key,val in self.dic.items():
            ns = string.replace(s, key, val)
            s = ns
        return s

    def getlspci(self):
        if not self.lspci:
            p = ["lspci", "-nn"]
            self.lspci = self.runcommand(p)

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
            pciids = re.findall(r"v0000([0-9A-Z]+)d0000([0-9A-Z]+)s", s)
            #USB: v*p*d => [('0CF3', '1002')]
            usbids = re.findall(r"v([0-9A-Z]+)p([0-9A-Z]+)d", s)
            if pciids:
                #04:01.0 Ethernet controller [0200]: Realtek Semiconductor Co., Ltd. RTL-8139/8139C/8139C+ [10ec:8139] (rev 10)
                mp = ":\s(.*%s:%s.*)" % (pciids[0][0], pciids[0][1])
                pcidesc = re.findall(mp, self.lspci, re.M + re.I)
                netcards.append("%s: %s" % (name, pcidesc[0]))
            if usbids:
                #Bus 002 Device 004: ID 0cf3:1002 Atheros Communications, Inc. TP-Link TL-WN821N v2 [Atheros AR9001U-(2)NG]
                mu = ":\sID\s(%s:%s.*)" % (usbids[0][0], usbids[0][1])
                usbdesc = re.findall(mu, self.lsusb, re.M + re.I)
                netcards.append("%s: %s" % (name, usbdesc[0]))
        network = ', '.join(netcards)
        return network

    def getdisplayinfo(self):
        match = re.findall(r"VGA[^:]+:\s+(.+)", self.lspci, re.M)
        graphics = ', '.join(match)
        return graphics

    def getcpuinfo(self):
        f = "/proc/cpuinfo"
        s = self.getfile(f)
        match = re.findall(r"model name\s+:\s+(.+)", s, re.M)
        x = match[0]
        num = len(match) # Number of the cpu cores
        cpu = "CPU: %sx %s" % (num, x)
        return cpu

    def getmeminfo(self):
        f = "/proc/meminfo"
        s = self.getfile(f)
        match = re.search(r"MemTotal:\s+(\d+)", s, re.M)
        x = int(match.group(1)) # kilobytes, convert string to int
        memory = x / 1024 # megabytes
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
        p = subprocess.Popen(command, stdout=subprocess.PIPE)
        output = p.communicate()[0]
        return output

class siggui:
    """ The graphical user interface for timekpr configuration. """
    def __init__(self, text):
        self.unknown = u"�"
        self.username = ""
        self.password = ""
        # UI FILE
        self.uifile = "ubuntu-gr_forum_signature.glade"
        self.builder = gtk.Builder()
        self.builder.add_from_file(self.uifile)
        #SIGNALS
        self.builder.connect_signals(self)
        # WINDOW
        self.window = self.builder.get_object("window1")
        self.textbox = self.builder.get_object("textview1") # new/pending sig
        self.textboxbuf = self.textbox.get_buffer()
        self.textboxbuf.set_text(text)
        self.textbox2 = self.builder.get_object("textview2") # old sig
        self.textboxbuf2 = self.textbox2.get_buffer()
        self.comboboxlinux = self.builder.get_object("comboboxentry1")
        self.comboboxprogramming = self.builder.get_object("comboboxentry2")
        self.comboboxenglish = self.builder.get_object("comboboxentry3")
        self.statusbar = self.builder.get_object("statusbar1")
        self.statusbarcid = self.statusbar.get_context_id("status")
        self.oldsigpack = self.builder.get_object("expander1")
        # DIALOG
        self.dialog = self.builder.get_object("dialog1")
        self.dialog.set_default_response(gtk.RESPONSE_CANCEL)
        self.entry1 = self.builder.get_object("entry1")
        self.entry2 = self.builder.get_object("entry2")
        # ERROR MESSAGE DIALOG
        self.errormsg = self.builder.get_object("messagedialog1")

    def statusmsg(self, message):
        msg = "%s %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), message)
        msgid = self.statusbar.push(self.statusbarcid, msg)
        #self.statusrefresh()
        timeoutid2 = glib.timeout_add_seconds(4, self.statusrefresh, msgid)

    def statusrefresh(self, msgid):
        self.statusbar.remove_message(self.statusbarcid, msgid)
    
    def gtk_main_quit(self, widget):
        gtk.main_quit()

    def on_comboboxentry_changed(self, widget):
        linux = self.comboboxlinux.get_active_text()
        programming = self.comboboxprogramming.get_active_text()
        english = self.comboboxenglish.get_active_text()
        self.line = u"Γνώσεις ⇛ Linux: %s ┃ Προγραμματισμός: %s ┃ Αγγλικά: %s" % \
            (linux, programming, english)
        (start, end) = self.textboxbuf.get_bounds()
        oldtext = self.textboxbuf.get_text(start, end) # get all text
        newtext = re.subn(
            r'Γνώσεις ⇛ Linux:.*┃ Προγραμματισμός:.*┃ Αγγλικά:.*',
            self.line,
            oldtext
        ) # newtext is a touple ("newstring", times_of_substitution)
        if newtext[1] > 0: # If substitutions took place
            self.textboxbuf.set_text(newtext[0])
        else: # If no substitutions took place
            if oldtext == "":
                self.textboxbuf.set_text(self.line)
            else:
                self.textboxbuf.set_text("%s\n%s" % (oldtext, self.line))

    def on_button3_clicked(self, widget):
        # Refresh
        pass

    def on_button1_clicked(self, widget):
        # Submit to forum
        dialogreply = self.dialog.run()
        if dialogreply == gtk.RESPONSE_APPLY:
            #print("REPLY: %s (continue)" % dialogreply)
            #print("User: %s Pass: %s" % (self.username, self.password))
            self.statusmsg("Contacting forum...")
            timeid = glib.timeout_add_seconds(1, self.webwrapper)
        #elif dialogreply == gtk.RESPONSE_CANCEL or dialogreply == gtk.RESPONSE_DELETE_EVENT:
            #print("REPLY: %s (cancel)" % dialogreply)
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
        self.dialog.response(gtk.RESPONSE_CANCEL)

    def gtk_true(self, *widget):
        # DIALOG - Continue
        self.dialog.response(gtk.RESPONSE_APPLY)

    def on_entry1_changed(self, widget):
        # DIALOG - Username
        self.username = self.entry1.get_text()

    def on_entry2_changed(self, widget):
        # DIALOG - Password
        self.password = self.entry2.get_text()

    def messagedialog(self, msg):
        self.errormsg.set_markup(msg)
        dialogreply = self.errormsg.run()
        self.errormsg.hide()

    def sendtoweb(self):
        (start, end) = self.textboxbuf.get_bounds()
        text = self.textboxbuf.get_text(start, end)

        try:
            m = __import__("mechanize")
        except ImportError:
            return (1,u"Σφάλμα: Δεν έχετε εγκατεστημένο το python-mechanize.\nΓια να αποσταλεί η υπογραφή σας πρέπει να εγκαταστήσετε το πακέτο/πρόγραμμα python-mechanize")
        br = m.Browser()
        br.set_handle_referer(True)
        br.set_handle_redirect(True)
        br.set_handle_equiv(True)
        #br.set_handle_gzip(True)
        br.set_handle_refresh(m._http.HTTPRefreshProcessor(), max_time=1)

        br.open("http://forum.ubuntu-gr.org/ucp.php?i=profile&mode=signature")
        #self.statusmsg("Logging in...")
        br.select_form(nr=1) # Select login form (no name for the form)
        br["username"] = self.username
        br["password"] = self.password
        response1 = br.submit()
        h1 = response1.read()

        m = re.search(r'<div class="error">(.*)</div>', h1)
        if m:
            errormsg = m.group(1)
            if re.search(r"Έχετε υπερβεί το μέγιστο αριθμό προσπαθειών σύνδεσης", errormsg):
                errormsg = u'Έχετε υπερβεί το μέγιστο αριθμό προσπαθειών σύνδεσης. Εκτός από το όνομα μέλους και τον κωδικό πρόσβασης σας τώρα επίσης πρέπει να εισαγάγετε και τον κώδικα επιβεβαίωσης.\nΓια να συνεχίσετε να χρησιμοποιείτε το πρόγραμμα, πρέπει να κάνετε login/σύνδεση στην ιστοσελίδα του φόρουμ, <a href="http://forum.ubuntu-gr.org">http://forum.ubuntu-gr.org</a>'
            self.statusmsg(u"Σφάλμα: %s" % errormsg)
            self.messagedialog(u"Σφάλμα: %s" % errormsg)
            return (1,u"Σφάλμα: %s" % errormsg)
            #print("Error: %s" % errormsg)
        #print(h1)

        r2 = br.follow_link(url_regex=r'.*profile.*mode=signature.*sid')
        #h2 = r2.read()
        #print(h2)

        br.select_form(nr=1)
        oldsigtmp = br["signature"]
        oldsig = unicode(oldsigtmp, "utf-8")
        br["signature"] = text
        r3 = br.submit(name='submit')
        h3 = r3.read()
        #print(h3)

        m = re.search(r'<p class="error">(.*)</p>', h3)
        if m:
            errormsg = m.group(1)
            self.statusmsg(u"Σφάλμα: %s" % errormsg)
            self.messagedialog(u"Σφάλμα: %s" % errormsg)
            return (1,u"Σφάλμα: %s" % errormsg)

        r4 = br.follow_link(url_regex=r'ucp\.php.*mode=logout')
        #h4 = r4.read()
        #print(h4)

        self.statusmsg("Submitted to forum!")
        return (0,oldsig)

def main():
    text = core().returnall()
    print(text)
    #sendtoweb(signature=text)
    siggui(text)
    gtk.main()

def timeit():
    #import cProfile
    #cProfile.run('main()')
    import timeit
    t = timeit.Timer('main()', 'from __main__ import main')
    print(t.timeit(number=1000))

if __name__ == "__main__":
    main()
    #timeit()
