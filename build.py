"""Run this after changes have been merged, to update the OTF font file.

This requires the FontForge Python bindings installed.
"""
from __future__ import print_function

import sys
import fontforge

SOURCE = "xkcd.sfd"
TARGET = "build/xkcd.otf"

font = fontforge.open(SOURCE)
font.generate(TARGET)
print("Built", TARGET)
