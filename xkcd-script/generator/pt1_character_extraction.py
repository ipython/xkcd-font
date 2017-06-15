import os
#import matplotlib.pyplot as plt
from skimage.color import rgb2gray
import scipy.ndimage.measurements
from skimage import measure
import numpy as np
from scipy import ndimage as ndi

import skimage.io



#handwriting_img = plt.imread('handwriting_minimal.png')
handwriting_img = skimage.io.imread('handwriting_minimal.png')
handwriting_img_gray = rgb2gray(handwriting_img)

labels, _ = ndi.label(handwriting_img_gray < 1)

stroke_locations = measure.regionprops(labels)

from collections import OrderedDict, namedtuple

Metric = namedtuple('Metric', ['maxx', 'maxy', 'minx', 'miny', 'withinx', 'withiny'])



def merge_images(img1, img1_bbox, img2, img2_bbox):
    """
    A function to merge together two images with different bounding boxes.

    """
    # The new image bounding box.
    bbox = (min([img1_bbox[0], img2_bbox[0]]),
            min([img1_bbox[1], img2_bbox[1]]),
            max([img1_bbox[2], img2_bbox[2]]),
            max([img1_bbox[3], img2_bbox[3]]))
    
    # The new image shape.
    shape = (bbox[2] - bbox[0], bbox[3] - bbox[1], 3)
    
    # The slice for image 1 inside of the new image array.
    img1_slice = [slice(img1_bbox[0] - bbox[0], img1_bbox[2] - bbox[0]),
                  slice(img1_bbox[1] - bbox[1], img1_bbox[3] - bbox[1])]
    
    # The slice for image 2 inside of the new image array.
    img2_slice = [slice(img2_bbox[0] - bbox[0], img2_bbox[2] - bbox[0]),
                  slice(img2_bbox[1] - bbox[1], img2_bbox[3] - bbox[1])]

    # Construct the new image, and fill it with white.
    merged_image = np.empty(shape, dtype=np.uint8)
    merged_image.fill(255)
    
    # Use all of image 1 and just drop it into the correct location within the new image.
    merged_image[img1_slice] = img1
    
    # We can't use the same approach for image 2, as it potentially overlaps with image 1.
    # Instead we use the parts of image 2 that aren't at the maximum of each color channel. 
    merged_image[img2_slice] = np.where(img2 != 255, img2,
                                        merged_image[img2_slice])
    
    return merged_image, bbox


def min_interval_distance(interval_1, interval_2):
    """
    Calculate the distance between two intervals.
    
       >>> min_interval_distance([0, 1], [2, 3])
       1
       >>> min_interval_distance([0, 1], [0.5, 3])
       0
       >>> min_interval_distance([10, 11], [5, 8])
       2
       >>> min_interval_distance([10, 11], [8, 5])
       2

    There is so much room for more elegance here, but hey-ho...

    """
    interval_1_sorted = sorted(interval_1)
    interval_2_sorted = sorted(interval_2)

    min_distance = min([np.abs(i_1 - i_2) for i_1 in interval_1 for i_2 in interval_2])
    within_1 = any(interval_1_sorted[0] <= i_2 <= interval_1_sorted[1] for i_2 in interval_2)    
    within_2 = any(interval_2_sorted[0] <= i_1 <= interval_2_sorted[1] for i_1 in interval_1)

    if within_1 or within_2:
        min_distance = 0
    return min_distance


def max_interval_distance(interval_1, interval_2):
    """
    Calculate the distance between two intervals.
    
       >>> max_interval_distance([0, 1], [2, 3])
       3
       >>> max_interval_distance([0, 1], [0.5, 3])
       3
       >>> max_interval_distance([10, 11], [5, 8])
       6
       >>> max_interval_distance([10, 11], [8, 5])
       6

    There is so much room for more elegance here, but hey-ho...

    """
    max_distance = max([np.abs(i_1 - i_2) for i_1 in interval_1 for i_2 in interval_2])
    return max_distance


def contains(interval_1, interval_2):
    """
    Whether one bounding box entirely contains another
    
       >>> contains([0, 4], [2, 3])
       True
       >>> contains([0, 1], [0.5, 3])
       False
       >>> contains([2, 3], [4, 0])
       True
    """
    interval_1_sorted = sorted(interval_1)
    interval_2_sorted = sorted(interval_2)

    within_1 = all(interval_1_sorted[0] <= i_2 <= interval_1_sorted[1] for i_2 in interval_2)    
    within_2 = all(interval_2_sorted[0] <= i_1 <= interval_2_sorted[1] for i_1 in interval_1)
    return within_1 or within_2


bbox_to_stroke_img = {}

for stroke in stroke_locations: 
    # [miny, minx, maxy, maxx] (I don't know why its that way around...)
    bbox = stroke.bbox

    # Construct a slice that can be used to pick out this bounding box from
    # the full image.
    full_index = [slice(bbox[0], bbox[2]), slice(bbox[1], bbox[3])]
    
    # Pick out the sub-image, and take a copy so that we can modify it without
    # modifying the original.
    stroke_img = handwriting_img[full_index + [Ellipsis]].copy()
    
    # Using the "labels" array, produce a binary mask that is True for every
    # pixel that is marked as this label, and False otherwise. 
    stroke_mask = labels[full_index] == stroke.label

    # For each color channel, use the mask to maintain the full image pixels that
    # are part of this stroke. Where a pixel remains that is not part of this stroke,
    # replace it with 1 (ultimately making it white).
    for channel in range(3):
        stroke_img[:, :, channel] = np.where(stroke_mask, stroke_img[:, :, channel], 1)
        
    # Convert the image to an RGB byte array.
    stroke_img = (stroke_img * 255).astype(np.uint8)

    bbox_to_stroke_img[bbox] = stroke_img


stroke_merge_contenders = {}

for bbox, img in bbox_to_stroke_img.items():
    height = bbox[2] - bbox[0]
    width = bbox[3] - bbox[1]
    if width < 450 and height < 150:
        stroke_merge_contenders[bbox] = img



# Track the images that ultimately got merged.
images_that_were_mergers = []

# Track the images that didn't find a merge buddy.
images_that_didnt_get_merged = []

# Take a copy of our existing images - we will remove merged strokes from here, and replace
# with the composite.
merged_bbox_to_stroke_img = bbox_to_stroke_img.copy()

# We could use an RTree for efficient nearest neighbour lookup, but just use a greedy search for now.
reduced_stroke_merge_contenders = stroke_merge_contenders.copy()


while reduced_stroke_merge_contenders:
    bbox, img = reduced_stroke_merge_contenders.popitem()
    
    # If we have already processed this file (as the right hand pair of a merge) then skip it.
    if bbox not in merged_bbox_to_stroke_img:
        continue
    
    # Remove this image from the final glyph set.
    merged_bbox_to_stroke_img.pop(bbox, None)

    candidates = []
    for other_bbox, other_img in list(merged_bbox_to_stroke_img.items()):
        if other_bbox == bbox:
            # We don't want to merge with ourselves.
            continue
        
        x_range, x_range_other = [other_bbox[1], other_bbox[3]], [bbox[1], bbox[3]]
        minx = min_interval_distance(x_range, x_range_other)
        miny = min_interval_distance([other_bbox[0], other_bbox[2]], [bbox[0], bbox[2]])
        
        maxx = max_interval_distance([other_bbox[1], other_bbox[3]], [bbox[1], bbox[3]])
        maxy = max_interval_distance([other_bbox[0], other_bbox[2]], [bbox[0], bbox[2]])
        
        withinx = contains([other_bbox[1], other_bbox[3]], [bbox[1], bbox[3]])
        withiny = contains([other_bbox[0], other_bbox[2]], [bbox[0], bbox[2]])
        
        metric = Metric(minx=minx, miny=miny, maxx=maxx, maxy=maxy, withinx=withinx, withiny=withiny)
        
        # The condition for which a pair of glyphs will be consiered for merging.
        # This took a significant amount of iteration to get a good performance.
        if (withinx and withiny) or \
                (((maxx < 250 or minx == 0) and minx < 10) and miny < 50) or \
                (other_bbox in reduced_stroke_merge_contenders and minx == 0 and maxy < 350):    
            candidates.append([metric, other_bbox, other_img])

    if not candidates:
        images_that_didnt_get_merged.append([img, bbox])
        # Put the stroke back into the new_bboxes so that we don't loose it.
        merged_bbox_to_stroke_img[bbox] = img
    else:
        # Prefer the candidates with a small maximum x over anything else.
        candidates.sort(key=lambda candidate: (candidate[0].maxx, candidate))

        metric, other_bbox, other_img = candidates[0]
        merged_image, merged_bbox = merge_images(img, bbox, other_img, other_bbox)

        # We're done with the other image too - remove it from the results.
        merged_bbox_to_stroke_img.pop(other_bbox)

        # If the resulting image is *tiny* then consider putting it back
        # into the pool of items that may be merged. This really is only of
        # value to the sprinkles within the cupcake. 
        height = merged_bbox[2] - merged_bbox[0]
        width = merged_bbox[3] - merged_bbox[1]
        if width < 100 and height < 100:
            reduced_stroke_merge_contenders[merged_bbox] = merged_image

        images_that_were_mergers.append(merged_bbox)
        merged_bbox_to_stroke_img[merged_bbox] = merged_image



import os.path
import skimage.io

strokes_dir = '../generated/strokes'
if not os.path.exists(strokes_dir):
    os.makedirs(strokes_dir)

for bbox, img_array in merged_bbox_to_stroke_img.items():
    fname = '../generated/strokes/stroke_x{1}_y{0}_x{3}_y{2}.png'.format(*bbox)
    skimage.io.imsave(fname, img_array)
