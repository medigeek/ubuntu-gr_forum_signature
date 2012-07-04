#!/usr/bin/python
import platform
import subprocess

if platform.python_version() < '2.5':
    exit('ERROR: You need python 2.5 or higher to use this program.')
if platform.system() != "Linux":
    exit('ERROR: This script is built for GNU/Linux platforms (for now)')

gtk3 = True
try:
    from gi.repository import Gtk, Gdk
except ImportError:
    log.error("Could not load gtk3 module. Using old gtk2.\n")
    gtk3 = False

if gtk3:
    # Start gtk3
    import forum_signature_gtk3
    forum_signature_gtk3.main()
else:
    # Start gtk2
    import forum_signature
    forum_signature.main()

