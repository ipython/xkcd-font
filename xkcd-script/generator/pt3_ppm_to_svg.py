# -*- coding: utf-8 -*-

from __future__ import division
import subprocess
import fontforge

def potrace(input_fname, output_fname):
    subprocess.check_call(['potrace', '-s', input_fname, '-o', output_fname])


import os
import glob

for fname in glob.glob('../generated/characters/char_*.ppm'):
    new_name = os.path.splitext(fname)[0] + '.svg'
    potrace(fname, new_name)

