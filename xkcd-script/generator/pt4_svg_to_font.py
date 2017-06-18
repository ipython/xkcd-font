# -*- coding: utf-8 -*-
from __future__ import division
import fontforge
import os
import glob
import parse

fnames = sorted(glob.glob('../generated/characters/char_*.svg'))

characters = []
for fname in fnames:
    # Sample filename: char_L2_P2_x378_y1471_x766_y1734_RQ==?.svg
    
    pattern = 'char_L{line:d}_P{position:d}_x{x0:d}_y{y0:d}_x{x1:d}_y{y1:d}_{b64_str}.svg'
    result = parse.parse(pattern, os.path.basename(fname))
    chars = tuple(result['b64_str'].decode('base64').decode('utf-8'))
    bbox = (result['x0'], result['y0'], result['x1'], result['y1'])
    characters.append([result['line'], result['position'], bbox, fname, chars])


def basic_font():
    font = fontforge.font()
    font.familyname = font.fontname = 'XKCD'
    font.encoding = "UnicodeFull"

    font.version = '1.0';
    font.weight = 'Regular';
    font.fontname = 'xkcdScript'
    font.familyname = 'xkcd Script'
    font.fullname = 'xkcd-Script-Regular'
    # Fontforge includes the date of building the font if we don't specify a TTF uniqueid,
    # which makes the font non-reproducible.
    font.sfnt_names = (('English (US)', 'UniqueID', 'xkcd Script'), )
    font.copyright = 'Copyright (c) ipython/xkcd-font contributors, Creative Commons Attribution-NonCommercial 3.0 License'
    # As per guidelines in https://fontforge.github.io/fontinfo.html, xuid is no longer needed.
    font.uniqueid = -1

    font.em = 1024;
    font.ascent = 768;
    font.descent = 256;

    # We create a ligature lookup table.
    font.addLookup('ligatures', 'gsub_ligature', (), [[b'liga',
                                                       [[b'latn',
                                                         [b'dflt']]]]])
    font.addLookupSubtable('ligatures', 'liga')
   
    return font



from contextlib import contextmanager
import tempfile
import shutil
import os


@contextmanager
def tmp_symlink(fname):
    """
    Create a temporary symlink to a file, so that applications that can't handle
    unicode filenames don't barf (I'm looking at you font-forge)
    
    """
    target = tempfile.mktemp(suffix=os.path.splitext(fname)[1])
    fname = os.path.normpath(os.path.abspath(fname))
    try:
        os.symlink(fname, target)
        yield target
    finally:
        if os.path.exists(target):
            os.remove(target)


def create_char(font, chars, fname):
    if len(chars) == 1:
        # A single unicode character, so I create a character in the font for it.

        # Because I'm using an old & narrow python (<3.5) I need to handle the unicode
        # characters that couldn't be converted to ordinals (so I kept them as integers). 
        if isinstance(chars[0], int):
            c = font.createMappedChar(chars[0])
        else:
            c = font.createMappedChar(ord(chars[0]))
    else:
        # Multiple characters - this is a ligature. We need to register this in the
        # ligature lookup table we created. Not all font-handling libraries will do anything
        # with ligatures (e.g. matplotlib doesn't at vn <=2)
        char_names = [charname(char) for char in chars]
        ligature_name = '_'.join(char_names)
        ligature_tuple = tuple([character.encode('ascii') for character in chars])
        ligature_tuple = tuple([character for character in char_names])
        
        c = font.createChar(-1, ligature_name)

        c.addPosSub('liga', ligature_tuple)

    c.clear()
        
    # Use the workaround to have non-unicode filenames.
    with tmp_symlink(fname) as tmp_fname:
        # At last, bring in the SVG image as an outline for this glyph.
        c.importOutlines(tmp_fname)

    return c


baseline_chars = ['a' 'e', 'm', 'A', 'E', 'M', '&', '@', '.', u'≪', u'É']
caps_chars = ['S', 'T', 'J', 'k', 't', 'l', 'b', 'd', '1', '2', u'3', u'≪', '?', '!']

line_stats = {}
for line, position, bbox, fname, chars in characters:
    if len(chars) == 1:
        this_line = line_stats.setdefault(line, {})
        char = chars[0]
        if char in baseline_chars:
            this_line.setdefault('baseline', []).append(bbox[3])
        if char in caps_chars:
            this_line.setdefault('cap-height', []).append(bbox[1])


import numpy as np
import psMat

def scale_glyph(char, char_bbox, baseline, cap_height):
    # TODO: The code in this function is convoluted - it can be hugely simplified.
    # Essentially, all this function does is figure out how much
    # space a normal glyph takes, then looks at how much space *this* glyph takes.
    # With that magic ratio in hand, I now look at how much space the glyph *currently*
    # takes, and scale it to the full EM. On second thoughts, this function really does
    # need to be convoluted, so maybe the code isn't *that* bad...
    
    font = char.font
    
    # Get hold of the bounding box information for the imported glyph.
    import_bbox = c.boundingBox()
    import_width, import_height = import_bbox[2] - import_bbox[0], import_bbox[3] - import_bbox[1]
    
    # Note that timportOutlines doesn't guarantee glyphs will be put in any particular location,
    # so translate to the bottom and middle.
    
    target_baseline = char.font.descent
    top = char.font.ascent
    top_ratio = top / (top + target_baseline)
    
    y_base_delta_baseline = char_bbox[3] - baseline
    
    width, height = char_bbox[2] - char_bbox[0], char_bbox[3] - char_bbox[1]

    # This is the scale factor that font forge will have used for normal glyphs...
    scale_factor = (top + target_baseline) / (cap_height - baseline)
    glyph_ratio = (cap_height - baseline) / height
    
    # A nice glyph size, in pixels. NOTE: In pixel space, cap_height is smaller than baseline, so make it positive.
    full_glyph_size = -(cap_height - baseline) / top_ratio
    
    to_canvas_coord_from_px = full_glyph_size / font.em
    
    anchor_ratio = (top + target_baseline) / height
    
    # pixel scale factor
    px_sf = (top + target_baseline) / font.em
    
    frac_of_full_size = (height / full_glyph_size)
    import_frac_1000 = font.em / import_height
    
    t = psMat.scale(frac_of_full_size * import_frac_1000)
    c.transform(t)


def translate_glyph(c, char_bbox, cap_height, baseline):
    # Put the glyph in the middle, and move it relative to the baseline.

    # Compute the proportion of the full EM that cap_height - baseline should consume.
    top_ratio = c.font.ascent / (c.font.ascent + c.font.descent)
    
    # In the original pixel coordinate space, compute how big a nice full sized glyph
    # should be.
    full_glyph_size = -(cap_height - baseline) / top_ratio
    
    # We know that the scale of the glyph is now good. But it is probably way off in terms of x & y, so we
    # need to fix up its position.
    glyph_bbox = c.boundingBox()
    # No matter where it is currently, take the glyph to x=0 and a y based on its positioning in
    # the original handwriting sample.
    t = psMat.translate(-glyph_bbox[0], -glyph_bbox[1] + ((baseline - char_bbox[3]) * c.font.em / full_glyph_size))
    c.transform(t)

    # Put horizontal padding around the glyph. I choose a number here that looks reasonable,
    # there are far more sophisticated means of doing this (like looking at the original image,
    # and calculating how much space there should be).
    space = 20
    scaled_width = glyph_bbox[2] - glyph_bbox[0] 
    c.width = scaled_width + 2 * space
    t = psMat.translate(space, 0)
    c.transform(t)


def charname(char):
    # Give the fontforge name for the given character.
    return fontforge.nameFromUnicode(ord(char))


def autokern(font):
    # Let fontforge do some magic and figure out automatic kerning for groups of glyphs.

    all_glyphs = [glyph.glyphname for glyph in font.glyphs()
                  if not glyph.glyphname.startswith(' ')]    

    #print('\n'.join(sorted(all_glyphs)))
    ligatures = [name for name in all_glyphs if '_' in name]
    upper_ligatures = [ligature for ligature in ligatures if ligature.upper() == ligature]
    lower_ligatures = [ligature for ligature in ligatures if ligature.lower() == ligature]
    
    caps = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ') + upper_ligatures
    lower = list('abcdefghijklmnopqrstuvwxyz') + lower_ligatures
    all_chars = caps + lower

    # Add a kerning lookup table.
    font.addLookup('kerning', 'gpos_pair', (), [[b'kern', [[b'latn', [b'dflt']]]]])
    font.addLookupSubtable('kerning', 'kern')
    
    # Everyone knows that two slashes together need kerning... (even if they didn't realise it)
    font.autoKern('kern', 150, [charname('/'), charname('\\')], [charname('/'), charname('\\')])

    font.autoKern('kern', 60, ['r', 's'], lower, minKern=50)
    font.autoKern('kern', 100, ['f'], lower, minKern=50)
    font.autoKern('kern', 60, lower, ['g'], minKern=50)
    font.autoKern('kern', 180, all_chars, ['j'], minKern=35)
    
    font.autoKern('kern', 150, ['T', 'F', 'J'], all_chars)
    font.autoKern('kern', 30, ['C'], all_chars)


font = basic_font()
font.ascent = 600;

# Pick out particular glyphs that are more pleasant than their latter alternatives.
special_choices = {('C', ): dict(line=4),
                   ('G',): dict(line=4),
                   # Get rid of the "as" ligature - it's not very good.
                   ('a', 's'): dict(line=None),
                   # A nice tall I.
                   ('I', ): dict(line=4),
                   }

# Special case - add a vertial pipe by re-using an I, and stretching it a bit.
for line, position, bbox, fname, chars in characters:
    if chars == (u'I',) and line == 4:
        characters.append([4, None, bbox, fname, ('|',)])

for line, position, bbox, fname, chars in characters:
    if chars in special_choices:
        spec = special_choices[chars]
        spec_line = spec.get('line', any)
        if spec_line is not any and spec_line != line:
            continue
        
    c = create_char(font, chars, fname)

    # Get the linestats for this character.
    line_features = line_stats[line]

    scale_glyph(
        c, bbox,
        baseline=np.mean(line_features['baseline']),
        cap_height=np.mean(line_features['cap-height']))
    
    translate_glyph(
        c, bbox,
        baseline=np.mean(line_features['baseline']),
        cap_height=np.mean(line_features['cap-height']))

    # Simplify, then put the vertices on rounded coordinate positions.
    c.simplify()
    c.round()

c = font.createMappedChar(32)
c.width = 256

autokern(font)
font_fname = '../font/xkcd-script.sfd'

if not os.path.exists(os.path.dirname(font_fname)):
    os.makedirs(os.path.dirname(font_fname))
if os.path.exists(font_fname):
    os.remove(font_fname)
font.generate(font_fname)

