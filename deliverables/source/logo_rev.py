"""Reversed (on-dark) version of the כח התערבות logo: ink -> off-white, gold block kept."""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

src, out = sys.argv[1], sys.argv[2]
im = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
H, W, _ = im.shape
r, g, b = im[..., 0], im[..., 1], im[..., 2]
lum = 0.2126 * r + 0.7152 * g + 0.0722 * b

# background = near-white region connected to the image border
near_white = im.min(2) > 225
lab, _ = ndimage.label(near_white)
border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
bg = np.isin(lab, border[border > 0])

# gold block: bounding box of saturated yellow pixels
gold = (r > 170) & (g > 130) & (b < 140) & (r - b > 80)
ys, xs = np.where(gold)
gx0, gx1, gy0, gy1 = xs.min(), xs.max(), ys.min(), ys.max()
in_block = np.zeros((H, W), bool); in_block[gy0:gy1 + 1, gx0:gx1 + 1] = True

ink_lum = 55.0  # navy
alpha = np.clip((255 - lum) / (255 - ink_lum), 0, 1)
rgba = np.zeros((H, W, 4), np.float32)
rgba[..., :3] = 242  # off-white ink
rgba[..., 3] = alpha * 255
# the gold block keeps its original colours and is fully opaque (except the outside corners)
# only the block's rounded top-left corner is see-through; the white book pages stay white
R = 56.0
yy, xx = np.mgrid[0:H, 0:W]
cx, cy = gx0 + R, gy0 + R
corner = (xx < cx) & (yy < cy) & (np.hypot(xx - cx, yy - cy) > R)
blk = in_block & ~corner
rgba[blk, :3] = im[blk]
rgba[blk, 3] = 255

ys, xs = np.where(rgba[..., 3] > 8)
pad = 12
crop = rgba[ys.min() - pad:ys.max() + pad, xs.min() - pad:xs.max() + pad]
Image.fromarray(crop.astype(np.uint8), "RGBA").save(out)
print("logo", crop.shape, "gold block", gx0, gx1, gy0, gy1)
