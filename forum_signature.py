#!/usr/bin/python
# -*- coding: utf-8 -*-
# File: forum_signature.py
# Purpose: Proposes a signature with useful hardware/software information to forum newcomers/newbies
# Requires: python 2.5, python-gtk2, python-mechanize

# Copyright (c) 2010-2011 Savvas Radevic <vicedar@gmail.com>
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
1 Γνώσεις → Linux: � ┃ Προγραμματισμός: � ┃ Αγγλικά: �
2 Λειτουργικά → Ubuntu 11.04 natty 64bit wubi (en_GB.utf8), Ubuntu 2.6.35-28-generic, Windows 7
3 Προδιαγραφές → 2x Intel Core2 Duo CPU E6550 2.33GHz ‖ RAM 3961 MiB ‖ MSI MS-7235
4 Κάρτες γραφικών: nVidia G73 [GeForce 7300 GT] [10de:0393] (rev a1)
5 Δίκτυα: eth0: Realtek RTL-8110SC/8169SC Gigabit Ethernet [10ec:8167] (rev 10) ⋮ eth1: Realtek RTL-8139/8139C/8139C+ [10ec:8139] (rev 10)
"""

import platform
pyversion = platform.python_version()
if pyversion < '2.5':
    exit('ERROR: You need python 2.5 or higher to use this program.')
if platform.system() != "Linux":
    exit('ERROR: This script is built for GNU/Linux platforms (for now)')

import sys
import os
import os.path
import re
import subprocess
import time
import glob

textonly = False
try:
    import pygtk
    pygtk.require('2.0')
    import gtk
except ImportError:
    sys.stderr.write("ERROR: Could not load gtk module\n")
    sys.stderr.flush()
    textonly = True
try:
    try:
        import gobject as glib
    except ImportError:
        import glib
except ImportError:
    sys.stderr.write("ERROR: Could not load glib/gobject module\n")
    sys.stderr.flush()
    textonly = True

class core:
    def __init__(self, osgrubber):
        self.osgrubbertuple = osgrubber
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
            "Acer, Inc.": "Acer",
            "Atheros Inc.": "Atheros",
            "ATI Technologies Inc": "ATI",
            "Gigabyte Technology Co., Ltd.": "Gigabyte",
            "VIA Technologies, Inc.": "VIA",
            "ASUSTeK Computer": "ASUS",
            "Intel Corporation": "Intel",
            "Apple Inc.": "Apple",
            "American Megatrends": "AMI?",
            "Phoenix Technologies": "Phoenix",
            "InnoTek": "Innotek",
            "Realtek Semiconductor Co., Ltd.": "Realtek",
            "nVidia Corporation": "nVidia",
            "ASUS INC.": "ASUS",
            "(R)": "",
            "(TM)": "",
            "(r)": "",
            "(tm)": "",
            "     ": " ",
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
        self.getlspci()
        self.getlsusb()
        self.getinfo()

    def printall(self):
        print(self.returnall())

    def returnall(self):
        x = self.knowledge()
        y = self.osinfo()
        z = self.specs()
        text = "%s\n%s\n%s" % (x, y, z)
        t = self.dicreplace(text)
        return t

    def knowledge(self):
        s = {   "linux": self.unknown,
                "programming": self.unknown,
                "english": self.unknown
            }
        return "1 Γνώσεις → Linux: %s ┃ Προγραμματισμός: %s ┃ Αγγλικά: %s" % \
                (s["linux"], s["programming"], s["english"])

    def osinfo(self):
        """ Calls osgrubber() class.
            Input: tuple list (osinfo, arch_type, iswubi, lang, self.oslist)
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
        s = "2 Λειτουργικά → %s (%s), %s" % (currosstr, lang, restofos)
        #print(s)
        return s

    def specs(self):
        core = self.shortencoreid()
        text = '3 Προδιαγραφές → %s ‖ RAM %s MiB ‖ %s\n4 Κάρτες γραφικών: %s\n5 Δίκτυα: %s' % \
            (self.info["cpu"],
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
        u2 = "%s %s" % (u, u) # "� �"
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
            "%s %s" % (self.coreid["board_vendor"], self.coreid["board_name"]),
            "%s %s" % (self.coreid["sys_vendor"], self.coreid["product_name"])
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
            pciids = re.findall("v0000([0-9A-Z]+)d0000([0-9A-Z]+)s", s)
            #USB: v*p*d => [('0CF3', '1002')]
            usbids = re.findall("v([0-9A-Z]+)p([0-9A-Z]+)d", s)
            append = netcards.append # PythonSpeed/PerformanceTips
            if pciids:
                #04:01.0 Ethernet controller [0200]: Realtek Semiconductor Co., Ltd. RTL-8139/8139C/8139C+ [10ec:8139] (rev 10)
                mp = ":\s(.*%s:%s.*)" % (pciids[0][0], pciids[0][1])
                pcidesc = re.findall(mp, self.lspci, re.M+re.I)
                append("%s: %s" % (name, pcidesc[0]))
            if usbids:
                #Bus 002 Device 004: ID 0cf3:1002 Atheros Communications, Inc. TP-Link TL-WN821N v2 [Atheros AR9001U-(2)NG]
                mu = ":\sID\s(%s:%s.*)" % (usbids[0][0], usbids[0][1])
                usbdesc = re.findall(mu, self.lsusb, re.M+re.I)
                append("%s: %s" % (name, usbdesc[0]))
        network = ' ⋮ '.join(netcards)
        return network

    def getdisplayinfo(self):
        m = re.compile("VGA[^:]+:\s+(.+)", re.M)
        match = m.findall(self.lspci)
        graphics = ' ⋮ '.join(match)
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
    def __init__(self, text, iswubi, debug=False):
        self.debug = debug
        self.is_wubi = iswubi
        self.unknown = "�"
        self.username = ""
        self.password = ""
        # UI FILE
        self.uifile = "forum_signature.glade"
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
        # BUG REPORT DIALOG
        self.reportbugdialog = self.builder.get_object("reportbug")
        self.textboxbuf3 = self.builder.get_object("textview3")
        # ERROR MESSAGE DIALOG
        self.errormsg = self.builder.get_object("messagedialog1")
        # Ubuntu Hardy 8.04 compatibility
        self.comboboxlinux.set_text_column(0)
        self.comboboxprogramming.set_text_column(0)
        self.comboboxenglish.set_text_column(0)
        # CHECK WUBI
        self.iswubi()

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
        sigtext = self.textboxbuf.get_text(start, end)

        text = "Περιγράψτε το πρόβλημα στη θέση αυτού του κειμένου.\n\
Επισυνάψτε σφάλμα από το τερματικό (αν υπάρχει).\n\n\
------------------------\n\
Πληροφορίες:[code]\n\
* cpuinfo\n{0}\n\
* meminfo:\n{1}\n\
* lspci:\n{2}\n\
* lsusb:\n{3}\n\
* signature:\n{4}\n\
[/code]".format(outcpu, outmem, outlspci, outlsusb, sigtext)

        # SAVE TO CLIPBOARD
        clipboard = gtk.clipboard_get()
        clipboard.set_text(text)
        clipboard.store()

        buf = self.textboxbuf3.get_buffer()
        buf.set_text(text)
        dialogreply = self.reportbugdialog.run()
        #print("%s %s" % (type(dialogreply), dialogreply))
        self.reportbugdialog.hide()

    def iswubi(self):
        # Check if its wubi
        if self.is_wubi == True:
            s = "<b>ΠΡΟΕΙΔΟΠΟΙΗΣΗ</b>: Δε συστήνεται η εγκατάσταση μέσω wubi."
            s2 = "Η εγκατάσταση που έχετε έγινε μέσω <span foreground='red'>wubi</span>. Τετοια εγκατάσταση συστήνεται μόνο για δοκιμαστικούς σκοπούς (<a href='http://wiki.ubuntu-gr.org/whynotwubi'>διαβάστε τους λόγους</a>).\nΔιαβάστε στους <a href='http://forum.ubuntu-gr.org/viewtopic.php?f=9&amp;t=859'>οδηγούς/how to/tutorials</a> πώς να κάνετε σωστή εγκατάσταση."
            self.messagedialog(s, s2)

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
        self.line = "Γνώσεις → Linux: %s ┃ Προγραμματισμός: %s ┃ Αγγλικά: %s" % \
            (linux, programming, english)
        (start, end) = self.textboxbuf.get_bounds()
        oldtext = self.textboxbuf.get_text(start, end) # get all text
        newtext = re.subn(
            'Γνώσεις → Linux:.*┃ Προγραμματισμός:.*┃ Αγγλικά:.*',
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

    def messagedialog(self, msg1, msg2):
        self.errormsg.set_markup(msg1)
        self.errormsg.format_secondary_markup(msg2)
        dialogreply = self.errormsg.run()
        self.errormsg.hide()

    def sendtoweb(self):
        (start, end) = self.textboxbuf.get_bounds()
        text = self.textboxbuf.get_text(start, end)

        try:
            m = __import__("mechanize")
        except ImportError:
            errormsg1 = "<b>ΣΦΑΛΜΑ</b>: Δεν έχετε εγκατεστημένο το python-mechanize."
            errormsg2 = "Για να αποσταλεί η υπογραφή σας πρέπει να εγκαταστήσετε το πακέτο/πρόγραμμα python-mechanize"
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
            import logging
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
                errormsg2 = 'Εκτός από το όνομα μέλους και τον κωδικό πρόσβασης σας τώρα επίσης πρέπει να εισαγάγετε και τον κώδικα επιβεβαίωσης. Για να συνεχίσετε να χρησιμοποιείτε το πρόγραμμα, πρέπει να κάνετε login/σύνδεση στην ιστοσελίδα του φόρουμ, <a href="http://forum.ubuntu-gr.org">http://forum.ubuntu-gr.org</a>'
                self.messagedialog("<b>ΣΦΑΛΜΑ</b>: %s" % errormsg1, errormsg2)
            else:
                self.messagedialog("<b>ΣΦΑΛΜΑ</b>: %s" % errormsg, "")
            self.statusmsg("Σφάλμα: %s" % errormsg)
            return (1,"Σφάλμα: %s" % errormsg)
            #print("Error: %s" % errormsg)
        #print(h1)

        r2 = br.follow_link(url_regex='.*profile.*mode=signature.*sid')
        #h2 = r2.read()
        #print(h2)

        br.select_form(nr=1)
        oldsig = br["signature"]
        br["signature"] = text
        #print(br.form)

        r3 = br.submit(name='submit')
        h3 = r3.read()
        #print(h3)

        m = re.search('<p class="error">(.*)</p>', h3)
        if m:
            errormsg = m.group(1)
            self.statusmsg("Σφάλμα: %s" % errormsg)
            self.messagedialog("Σφάλμα: %s" % errormsg, "")
            return (1,"Σφάλμα: %s" % errormsg)

        r4 = br.follow_link(url_regex='ucp\.php.*mode=logout')
        #h4 = r4.read()
        #print(h4)

        self.statusmsg("Submitted to forum!")
        return (0,oldsig)

class osgrubber:
    """ Retrieves information about installed operating systems. """
    def __init__(self):
        self.oslist = list()
        self.result = ""
        result = self.read_grub() # Sets self.oslist array
        self.finalize()

    def printall(self):
        import pprint
        pprint.pprint(self.result)

    def returnall(self):
        return self.result

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
            return True
        return False

    def finalize(self):
        """ Finalizes the processing.
            Returns a tuple list: (osinfo, arch_type, iswubi, lang, self.oslist)
        """
        iswubi = self.is_wubi()
        if self.is_wubi():
            wubi = "wubi"
        else:
            wubi = ""

        arch_type = self.machinearch()
        osinfo = self.osinfo()
        lang = self.oslang()

        #('Ubuntu 11.04 natty', '64bit', True, 'en_GB.utf8', ('Ubuntu 2.6.35-28-generic', 'Windows 7'))
        self.result = (osinfo, arch_type, iswubi, lang, self.oslist)

    def osinfo(self):
        # ('Ubuntu', '10.10', 'maverick')
        try:
            d = platform.linux_distribution()
        except AttributeError:
            d = platform.dist() # For python versions < 2.6
        distrib = ' '.join(d)
        return distrib

    def oslang(self):
        lang = os.getenv("LANG", "en_US") # Assume en_US if LANG var not set
        return lang  

    def machinearch(self):
        m = platform.architecture()
        #('64bit', 'ELF')
        return m[0]

    def read_grub(self):
        """ Retrieves operating systems from grub configuration file.
            Sets self.oslist array
            Returns True/False
        """
        #Does grub.cfg exist?
        grubcfg = "/boot/grub/grub.cfg"
        if not os.path.isfile(grubcfg):
            return False

        #getfile
        f = open(grubcfg, "r")
        a = list(f.readlines())
        lines = ''.join(a)
        f.close()
        #menuentry "Windows 7 (loader) (on /dev/sdc1)"
        #menuentry 'Ubuntu, with Linux 2.6.35-28-generic'
        matches = re.findall("^menuentry\s+['\"]([^'\"]*)['\"]", lines, re.M)
        if not matches:
            return False
        
        append = self.oslist.append # PythonSpeed/PerformanceTips
        for i in matches:
            # Drop memtest and recovery modes
            if not re.search("recovery|memtest|ανάκτηση", i, re.I):
                if re.search("linux", i, re.I):
                    #Ubuntu, with Linux 2.6.38-8-generic
                    osline = re.sub(",\s?(?:with|με)? Linux", "", i, re.I)
                elif re.search("windows", i, re.I):
                    #Windows 7 (on /dev/sdc1)
                    osline = re.search("(Windows(\s+[^\(]+)?)", i, re.I).group(0)
                    osline = osline.rstrip() # clear spaces on right side
                else:
                    osline = i
                if not self.is_currentos(osline):
                    append(osline)
        return True

    def is_wubi(self):
        # Detects wubi installation
        # Scans /etc/fstab for loop devices as root "/" and swap
        #return True # Uncomment this for testing
        fstabfile = "/etc/fstab" # /etc/fstab
        if not os.path.isfile(fstabfile):
            return False
        f = open(fstabfile, "r")
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
            sys.stderr.write("WARNING: wubi installation detected.\n")
            sys.stderr.flush()
            return True
        else:
            return False

def main():
    global textonly
    o = osgrubber().returnall()
    #(osinfo, arch_type, iswubi, lang, self.oslist)

    text = core(o).returnall()
    debug_app = False
    if len(sys.argv) > 1:
        if "--text" in sys.argv:
            textonly = True
        elif "--debug" in sys.argv:
            debug_app = True
    if textonly:
        print(text)
    else:
        print(text)
        siggui(text, o[2], debug=debug_app)
        gtk.main()

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

