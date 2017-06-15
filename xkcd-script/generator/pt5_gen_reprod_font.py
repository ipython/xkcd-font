"""
This script gives us reproducible builds of the fonts themselves, so that we don't recreate the font unnecessarily.

"""
import os

import fontforge


base = '../font/'
sfd = os.path.join(base, 'xkcd-script.sfd')
ttf = os.path.join(base, 'xkcd-script.ttf')
woff = os.path.join(base, 'xkcd-script.woff')

font = fontforge.open(ttf)
font.generate(woff)


if False:
    font.generate(sfd)
    content = []
    with open(sfd, 'rb') as fh_in:
        for line in fh_in:
            try:
                line = line.decode('utf-8')
            except UnicodeDecodeError:
                content.append(line)
                continue

            if line.startswith('%%CreationDate'):
                line = '%%CreationDate: Sat Jan 1 00:00:00 2000\n'

            if 'Created with FontForge (http://fontforge.org)' in line:
                line = '% Created with FontForge (http://fontforge.org)\n'

            content.append(line.encode('utf-8'))

    with open(sfd, 'wb') as fh_out:
        for line in content:
            fh_out.write(line)


for fn in [ttf, woff]:
    content = []
    with open(fn, 'rb') as fh_in:
        for line in fh_in:
            try:
                line = line.decode('utf-8')
            except UnicodeDecodeError:
                content.append(line)
                continue

            if line.startswith('CreationTime'):
                line = 'CreationTime: 1490000000\n'

            if line.startswith('ModificationTime'):
                line = 'ModificationTime: 1490000000\n'

            content.append(line.encode('utf-8'))

    with open(fn, 'wb') as fh_out:
        for line in content:
            fh_out.write(line)
