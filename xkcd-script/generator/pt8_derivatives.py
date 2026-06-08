# -*- coding: utf-8 -*-
"""
Orchestrate pt8 derivative-font steps.  Each pt8X_*.py script reads the
pt7 base SFD and either writes its own derivative SFD into ../generated/
or extracts data from the base to splice elsewhere.  Steps share no state
beyond the pt7 SFD.  Add a step by writing pt8X_<name>.py and appending
it to DERIVATIVES below.
"""
import pathlib
import runpy


HERE = pathlib.Path(__file__).parent

DERIVATIVES = [
    'pt8a_mathjax3.py',
]

for script in DERIVATIVES:
    print(f"### {script} ###")
    runpy.run_path(str(HERE / script), run_name='__main__')
