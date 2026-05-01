#!/usr/bin/env python3
"""Validate expected ligatures against the built OTF and emit preview text."""
import os
import sys

from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
OTF = os.path.join(HERE, '../font/xkcd-script.otf')

# (display_text, input_glyph_sequence)
EXPECTED = [
    ('co', ('c', 'o')),
    ('oo', ('o', 'o')),
    ('EA', ('E', 'A')),
    ('CO', ('C', 'O')),
    ('CR', ('C', 'R')),
    ('OCH', ('O', 'C', 'H')),
    ('TH', ('T', 'H')),
    ('TR', ('T', 'R')),
    ('TI', ('T', 'I')),
    ('EE', ('E', 'E')),
    ('TT', ('T', 'T')),
    ('LB', ('L', 'B')),
    ('ER', ('E', 'R')),
    ('RR', ('R', 'R')),
    ('LA', ('L', 'A')),
    ('LL', ('L', 'L')),
    ('ON', ('O', 'N')),
    ('CA', ('C', 'A')),
    ('PS', ('P', 'S')),
    ('TO', ('T', 'O')),
    ('|>', ('bar', 'greater')),
    ('<|', ('less', 'bar')),
    ('I-pronoun', ('I', 'hyphen', 'p', 'r', 'o', 'n', 'o', 'u', 'n')),
]

tt = TTFont(OTF)
gsub = tt['GSUB'].table

ligatures = set()
for record in gsub.FeatureList.FeatureRecord:
    if record.FeatureTag != 'liga':
        continue
    for idx in record.Feature.LookupListIndex:
        lookup = gsub.LookupList.Lookup[idx]
        if lookup.LookupType != 4:
            continue
        for sub in lookup.SubTable:
            for first, ligset in sub.ligatures.items():
                for lig in ligset:
                    ligatures.add((first,) + tuple(lig.Component))

expected_seqs = {seq for _, seq in EXPECTED}
uncovered = sorted(str(seq) for seq in ligatures if seq not in expected_seqs)
if uncovered:
    sys.exit('ERROR: font ligatures not in EXPECTED — add to gen_ligatures.py:\n' + '\n'.join(uncovered))

cols = 6
tokens = [display for display, _ in EXPECTED]
rows = [tokens[i:i + cols] for i in range(0, len(tokens), cols)]
print('Ligatures:\n' + '\n'.join('  ' + '  '.join(row) for row in rows))
