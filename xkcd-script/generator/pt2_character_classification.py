# -*- coding: utf-8 -*-

import glob
import os

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import numpy as np
import parse


pattern = 'stroke_x{x0:d}_y{y0:d}_x{x1:d}_y{y1:d}.png'
strokes_by_bbox = {}
for fname in glob.glob('../generated/strokes/stroke*.png'):
    result = parse.parse(pattern, os.path.basename(fname))
    bbox = (result['x0'], result['y0'], result['x1'], result['y1'])
    img = (plt.imread(fname) * 255).astype(np.uint8)
    strokes_by_bbox[bbox] = img


import scipy.cluster.vq

n_lines = 11

xs, ys = zip(*[[bbox[0], bbox[3]]
                for bbox, img in strokes_by_bbox.items()])
xs = np.array(xs, dtype=np.float)
ys = np.array(ys, dtype=np.float)

lines, _ = scipy.cluster.vq.kmeans(ys, n_lines, iter=1000)
lines = np.array(sorted(lines))

glyphs_by_line = [[] for _ in range(n_lines)]
for bbox, img  in list(strokes_by_bbox.items()):
    nearest_line = np.argmin(np.abs(bbox[3] - lines))
    glyphs_by_line[nearest_line].append([bbox, img])

# Put the glyphs in order from left-to-right.
for glyph_line in glyphs_by_line:
    glyph_line.sort(key=lambda args: args[0][0])



paragraph = r"""
a b c d e f g h i j k l m n o p q r s t u v w x y z
u n a u t h o r i t a t i v e n e s s   l e a t h e r b a r k   i n t r a co l i c   m i c r o c h e i l i a   o f f s i d e r
g l as s w e e d   r o t t o l o   a l b e r t i  t e   h e r m a t o r r h a c h i s   o r g a n o m e t a l l i c
s e g r e g a t i o n i s t   u n e v a n g e l i c   c a m p s t oo l
A B C D E F G H I J K L M N O P Q R S T U V W X Y Z I-pronoun
U N A U T H O R I T A T I V E N E S S   L EA T H E R B A R K   I N T R A CO L I C   M I CR OCH E L I A
O F F S I D ER   G LA S S W EE D   R O TT O L O   A LB E R T I T E   H ER M A T O RR H A C H I S
O R G A N O M E T A LL I C   S E G R E G A T I ON I S T   U N E V A N G E L I C   CA M PS TO O L
+ - x * ! ? # @ $ % ¦ & ^ _ - - - ( ) [ ] { } / \ < > ÷ ± √ Σ
1 2 3 4 5 6 7 8 9 0 ∫ = ≈ ≠ ~ ≤ ≥ |> <| 🎂 . , ; : “ H I ” ’ ‘ C A N ' T ' "
É Ò Å Ü ≪ ≫ ‽ Ē Ő “ ”
""".strip()
paragraphs = [[char for char in line.replace('   ', ' ').split(' ') if char]
              for line in paragraph.split('\n')]


glyphs_needing_two_strokes = ['≪', '≫', '|>', '<|']



def merge(img1, img1_bbox, img2, img2_bbox):
    bbox = (min([img1_bbox[0], img2_bbox[0]]),
            min([img1_bbox[1], img2_bbox[1]]),
            max([img1_bbox[2], img2_bbox[2]]),
            max([img1_bbox[3], img2_bbox[3]]),
            )
    shape = bbox[3] - bbox[1], bbox[2] - bbox[0], 3
    img1_slice = [slice(img1_bbox[1] - bbox[1], img1_bbox[3] - bbox[1]),
                  slice(img1_bbox[0] - bbox[0], img1_bbox[2] - bbox[0])]
    
    img2_slice = [slice(img2_bbox[1] - bbox[1], img2_bbox[3] - bbox[1]),
                  slice(img2_bbox[0] - bbox[0], img2_bbox[2] - bbox[0])]

    merged_image = np.zeros(shape, dtype=np.uint8)
    merged_image.fill(255)
    merged_image[img1_slice] = img1
    merged_image[img2_slice] = np.where(img2 != 255, img2, merged_image[img2_slice])
    return merged_image, bbox



characters_by_line = []

for line_no, (character_line, glyph_line) in enumerate(zip(paragraphs, glyphs_by_line)):
    glyph_iter = iter(glyph_line)
    characters_this_line = []
    characters_by_line.append(characters_this_line)

    for char_no, character in enumerate(character_line):
        bbox, img = next(glyph_iter)
        if character in glyphs_needing_two_strokes:
            other_bbox, other_img = next(glyph_iter)
            img, bbox = merge(img, bbox, other_img, other_bbox)
        characters_this_line.append([character, bbox, img])



import skimage.io

if not os.path.isdir('../generated/characters'):
    os.makedirs('../generated/characters')

replacements = {'/': 'forward-slash', '_': 'underscore'}

for line_no, line in enumerate(characters_by_line):
    for char_no, (char, bbox, img) in enumerate(line):
        char_repr = '-'.join(replacements.get(c, c) for c in char)
        hex_repr = '-'.join(str(hex(ord(c))) for c in char)
        b64_repr = char.encode('base64')

        fname = ('char_L{}_P{}_x{}_y{}_x{}_y{}_{b64_repr}.ppm'
                 ''.format(line_no, char_no, *bbox, b64_repr=b64_repr))
        fname = os.path.join('../generated/characters', fname)
        skimage.io.imsave(fname, img)
