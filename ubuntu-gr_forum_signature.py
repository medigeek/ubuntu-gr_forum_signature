#!/usr/bin/python
# -*- coding: utf-8 -*-
# File: ubuntu-gr_signature.py
# Purpose: Proposes a signature with useful hardware/software information to forum newcomers/newbies
# Requires: python 2.5, lshw, lsb-release, sudo (for motherboard chip recognition)
#           python-gtk2, python-mechanize

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

import os
import re
import subprocess
import xml.dom.minidom
import time

import pygtk
pygtk.require('2.0')
import gtk
import glib

class core:
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

    def printall(self):
        x = self.knowledge()
        y = self.osinfo()
        z = self.specs()
        print(u"%s\n%s\n%s" % (x, y, z))

    def returnall(self):
        x = self.knowledge()
        y = self.osinfo()
        z = self.specs()
        return u"%s\n%s\n%s" % (x, y, z)

    def knowledge(self):
        s = {   "linux": self.unknown,
                "programming": self.unknown,
                "english": self.unknown
            }
        return u"Γνώσεις ⇛ Linux: %s ┃ Προγραμματισμός: %s ┃ Αγγλικά: %s" % \
                (s["linux"], s["programming"], s["english"])

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
        return u"Λειτουργικό: %s %s %s (%s)" % \
                (distrib["id"], distrib["rel"], arch_type, lang)

    def specs(self):
        machine = self.shortenmachineid()
        return u'Προδιαγραφές ⇛ %s │ RAM %s MiB │ %s\nΚάρτες γραφικών: %s\nΔίκτυα: %s' % \
                (self.lshwinfo["cpu"],
                self.lshwinfo["memory"],
                machine,
                ', '.join(self.lshwinfo["display"]),
                ', '.join(self.lshwinfo["network"])
                )

    def oslang(self):
        lang = os.getenv("LANG", "en_US") # Assume en_US if LANG var not set
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

    def shortenmachineid(self):
        # Shorten the machine/motherboard id and manufacturer
        if self.lshwinfo["system"] == self.lshwinfo["core"]:
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
        elif re.match(r"InnoTek", tempa2, re.IGNORECASE):
            temp_final2 = "Innotek"
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
                sudocmd = self.choosesudo()
                self.lshwxml = self.runcommand([sudocmd, "--", "lshw", "-quiet", "-xml" , "-sanitize", "-numeric"])
            # Fix bug: https://bugs.launchpad.net/bugs/512251
            lines = self.lshwxml.split("\n")
            for l in lines:
                if re.search(r'id="lastmountpoint"', l):
                    lines.remove(l)
            self.lshwxml = '\n'.join(lines)

        doc = xml.dom.minidom.parseString(self.lshwxml)
        nodes = doc.getElementsByTagName("node")
        for n in nodes:
            if n.hasAttribute("class") and \
                n.getAttribute("class") == "system" and \
                n.hasAttribute("handle") and n.getAttribute("handle") == "DMI:0001":
                #<product>MS-7235</product><vendor>MICRO-STAR INTERNATIONAL CO.,LTD</vendor>
                #product: G31M-S2L - vendor: Gigabyte Technology Co., Ltd.

                product = n.getElementsByTagName("product")[0]
                # double check if we're in the same node as before
                if product.parentNode.getAttribute("handle") == "DMI:0001":
                    tempa1 = product.childNodes[0].nodeValue
                else:
                    tempa1 = ""

                vendor = n.getElementsByTagName("vendor")[0]
                # double check if we're in the same node as before
                if vendor.parentNode.getAttribute("handle") == "DMI:0001":
                    tempa2 = vendor.childNodes[0].nodeValue
                else:
                    tempa2 = ""

                temp_final2 = self.shortenmoboid(tempa2)

                # Clear/replace bad default motherboard values
                badmoboids = (
                    "to be filled by o.e.m.",
                    "system manufacturer",
                    "system product name"
                )
                try:
                    badmoboids.index(temp_final2.lower())
                    temp_final2 = ""
                except ValueError:
                    pass
                try:
                    badmoboids.index(tempa1.lower())
                    tempa1 = ""
                except ValueError:
                    pass

                if not temp_final2 and not tempa1:
                    self.lshwinfo["system"] = self.unknown
                elif not temp_final2 and tempa1:
                    self.lshwinfo["system"] = tempa1
                elif temp_final2 and not tempa1:
                    self.lshwinfo["system"] = temp_final2
                else:
                    self.lshwinfo["system"] = "%s %s" % (temp_final2, tempa1)
                #print("MOO: %s %s" % (tempa1, tempa2))
            
            if n.hasAttribute("id"):
                if n.getAttribute("id") == "core":
                    #<product>MS-7235</product><vendor>MICRO-STAR INTERNATIONAL CO.,LTD</vendor>
                    #product: G31M-S2L - vendor: Gigabyte Technology Co., Ltd.

                    product = n.getElementsByTagName("product")[0]
                    # double check if we're in the same node as before
                    if product.parentNode.getAttribute("id") == "core":
                        tempa1 = product.childNodes[0].nodeValue
                    else:
                        tempa1 = ""

                    vendor = n.getElementsByTagName("vendor")[0]
                    # double check if we're in the same node as before
                    if vendor.parentNode.getAttribute("id") == "core":
                        tempa2 = vendor.childNodes[0].nodeValue
                    else:
                        tempa2 = ""

                    temp_final2 = self.shortenmoboid(tempa2)
                    # Clear/replace bad default motherboard values
                    badmoboids = (
                        "to be filled by o.e.m.",
                        "system manufacturer",
                        "system product name"
                    )
                    try:
                        badmoboids.index(temp_final2.lower())
                        temp_final2 = ""
                    except ValueError:
                        pass
                    try:
                        badmoboids.index(tempa1.lower())
                        tempa1 = ""
                    except ValueError:
                        pass

                    if not temp_final2 and not tempa1:
                        self.lshwinfo["core"] = self.unknown
                    elif not temp_final2 and tempa1:
                        self.lshwinfo["core"] = tempa1
                    elif temp_final2 and not tempa1:
                        self.lshwinfo["core"] = temp_final2
                    else:
                        self.lshwinfo["core"] = "%s %s" % (temp_final2, tempa1)
                    #print("MOO2: %s %s %s" % (temp_final2, tempa1, tempa2))

                elif re.match(r'cpu', n.getAttribute("id")):
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

                elif re.match(r'display', n.getAttribute("id")):
                    identified = False
                    try:
                        tempmodel = n.getElementsByTagName("product")[0].childNodes[0].nodeValue
                        # G73 [GeForce 7300 GT], Radeon R350 [Radeon 9800 Pro]
                        tempa2 = n.getElementsByTagName("vendor")[0].childNodes[0].nodeValue
                        # nVidia Corporation, ATI Technologies Inc
                        identified = True
                    except IndexError:
                        pass

                    if identified:
                        tempvendor = tempa2
                        try:
                            if tempa2[0:6].lower() == "nvidia":
                                tempvendor = "nVidia"
                            elif tempa2[0:3].lower() == "ati":
                                tempvendor = "ATI"
                            elif tempa2[0:5].lower() == "intel":
                                tempvendor = "Intel"
                            elif tempa2[0:7].lower() == "innotek":
                                tempvendor = "Innotek"
                        except IndexError:
                            pass

                        displaystr = "%s %s" % (tempvendor, tempmodel)
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

                elif re.match(r'network', n.getAttribute("id")):
                    identified = False
                    try:
                        tempdesc = n.getElementsByTagName("description")[0].childNodes[0].nodeValue
                        # Wireless interface, Ethernet interface
                        tempmodel = n.getElementsByTagName("product")[0].childNodes[0].nodeValue
                        # PRO/Wireless 2200BG [Calexico2] Network Connection, L1 Gigabit Ethernet Adapter
                        tempa2 = n.getElementsByTagName("vendor")[0].childNodes[0].nodeValue
                        # Realtek Semiconductor Co., Ltd., Intel Corporation, Atheros Communications
                        identified = True
                    except IndexError:
                        pass

                    if identified:
                        cre = re.compile(r' interface', re.IGNORECASE)
                        temptype = cre.sub('', tempdesc)

                        tempvendor = tempa2
                        try:
                            if tempa2[0:6].lower() == "nvidia":
                                tempvendor = "nVidia"
                            elif tempa2[0:3].lower() == "via":
                                tempvendor = "VIA"
                            elif tempa2[0:7].lower() == "atheros":
                                tempvendor = "Atheros"
                            elif tempa2[0:5].lower() == "intel":
                                tempvendor = "Intel"
                            elif tempa2[0:7].lower() == "realtek":
                                tempvendor = "Realtek"
                            elif tempa2[0:8].lower() == "broadcom":
                                tempvendor = "Broadcom"
                        except IndexError:
                            pass

                        #tempmodel = cre.sub('', tempa1)

                        networkstr = "%s: %s %s" % (temptype, tempvendor, tempmodel)
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

                elif re.match(r'memory', n.getAttribute("id")):
                    try:
                        x = n.getElementsByTagName("description")[0].childNodes[0].nodeValue
                        #print("MOO1: %s" % x)
                        if x.lower() == "system memory":
                            tempa = n.getElementsByTagName("size")[0].childNodes[0].nodeValue
                            #print("MOO2: %s" % tempa)
                            tempmemory = int(tempa) / 1024**2 # Size in bytes, divide by 1024**2, result in MiB
                            self.lshwinfo["memory"] = tempmemory
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

        m = __import__("mechanize")
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
    #Argument: lshw xml filename (for testing)
    try:
        arg = sys.argv[1]
    except IndexError:
        arg = ""
    text = core(fxml=arg).returnall()
    print(text)
    #sendtoweb(signature=text)
    siggui(text)
    gtk.main()

if __name__ == "__main__":
    main()

