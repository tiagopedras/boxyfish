"""Isolate individual fish from the scanned sheets.

For each scan:
  1. flatten the paper (divide out a blurred background) so a yellowed scan
     thresholds the same as a clean white one
  2. find ink, close small gaps so a detached tail fin joins its body
  3. label connected blobs -> one blob per fish
  4. fill the body interior white, keep the ink lines, everything else alpha 0
  5. find the eye dot (small ink blob floating inside the body) and use it,
     plus the silhouette's long axis, to work out which way the fish points

The cut-out is saved exactly as drawn: the same proportions, the same slight
tilt, facing the same way. The heading is only recorded in the manifest, so
the aquarium can swim each fish along the axis it was drawn on.
"""

import json
import math
import os

import numpy as np
from PIL import Image
from scipy import ndimage

SRC = os.path.join(os.path.dirname(__file__), "..", "src")
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "fish")

CLOSE_RADIUS = 9      # px, gap-bridging distance at scan resolution
MIN_AREA = 900         # px, drop dust and pen specks
MIN_SIDE = 28          # px, drop anything too small to read
PAD = 6                # px of transparent margin around each crop
INK_LO, INK_HI = 0.32, 0.55   # soft-edge band for ink outside the body

# manual heading corrections, degrees clockwise from "pointing right".
# Use these when the automatic guess has a fish pointing the wrong way.
ANGLE_FIX = {
    "6_02.png": 170.0,   # tail is the loose quad on the right
    "6_05.png": 180.0,   # eye is on the left, wedge tail on the right
    "7_06.png": -20.0,   # follow the parallelogram, not the corner-to-corner
    "8_05.png": 0.0,     # body drawn upright, but it swims tail-left
    "8_06.png": 172.0,   # dome nose on the left, oval tail on the right
    "8_08.png": 175.0,   # speckled tail on the right
}

# Two drawings sitting close enough that step 2 bridged them into one blob.
# The rectangle, in fractions of the blob's bounding box, is the part that
# belongs to the second fish; the rest is the first. Pieces are saved as
# <name>a.png and <name>b.png so the other fish keep their numbering.
SPLITS = {
    "8_11.png": (0.00, 0.50, 0.46, 1.00),   # small fish sits below-left of the tube
}


def disk(r):
    y, x = np.ogrid[-r:r + 1, -r:r + 1]
    return x * x + y * y <= r * r


def ink_mask(gray):
    """Ink = pixels meaningfully darker than their local paper colour."""
    bg = ndimage.gaussian_filter(gray, sigma=60)
    inkness = np.clip(1.0 - gray / np.maximum(bg, 1e-6), 0, 1)
    return inkness > 0.28, inkness


def find_eye(ink_sub, body_sub):
    """The eye is the small round ink dot floating clear of the outline.

    Hatch marks on fins also float clear, so score candidates on roundness
    and prefer the smallest convincing dot.
    """
    lbl, n = ndimage.label(ink_sub)
    outline = ndimage.binary_dilation(
        body_sub ^ ndimage.binary_erosion(body_sub, disk(4)), disk(2))
    best = None
    for i in range(1, n + 1):
        blob = lbl == i
        area = int(blob.sum())
        if area < 6 or area > 0.01 * body_sub.sum():
            continue
        if (blob & outline).any():          # touches the outline: not an eye
            continue
        ys, xs = np.nonzero(blob)
        bh, bw = np.ptp(ys) + 1, np.ptp(xs) + 1
        if max(bh, bw) > 34 or min(bh, bw) < 2:
            continue
        if not 0.55 < bw / bh < 1.8:        # a dot is roughly square
            continue
        if area / float(bh * bw) < 0.55:    # and roughly fills its box
            continue
        score = area                        # smallest round dot wins
        if best is None or score < best[0]:
            best = (score, xs.mean(), ys.mean())
    return None if best is None else (best[1], best[2])


def orientation(body, eye):
    """Which way the fish points, in degrees clockwise from "right".

    Prefer the centroid -> eye direction when the eye sits clearly towards
    one end; otherwise fall back to the silhouette's long axis, pointed to
    whichever end the eye is on.
    """
    ys, xs = np.nonzero(body)
    cx, cy = xs.mean(), ys.mean()
    cov = np.cov(np.vstack([xs - cx, ys - cy]))
    vals, vecs = np.linalg.eigh(cov)
    ax = vecs[:, np.argmax(vals)]
    size = max(np.ptp(xs), np.ptp(ys))

    if eye is not None:
        to_eye = np.array([eye[0] - cx, eye[1] - cy])
        dist = np.linalg.norm(to_eye)
        if np.dot(ax, to_eye) < 0:
            ax = -ax
        # eye well off-centre and pointing away from the long axis ->
        # the drawing's long axis isn't the swimming axis, trust the eye
        if dist > 0.18 * size:
            cos = np.dot(ax, to_eye) / dist
            if cos < 0.72:
                ax = to_eye / dist
    return math.degrees(math.atan2(ax[1], ax[0]))


def process(path, sheet, records):
    img = Image.open(path).convert("L")
    gray = np.asarray(img, dtype=np.float32) / 255.0

    ink, inkness = ink_mask(gray)
    closed = ndimage.binary_closing(ink, disk(CLOSE_RADIUS))
    filled = ndimage.binary_fill_holes(closed)
    bodies = filled | ink

    lbl, n = ndimage.label(bodies)
    kept = 0
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lbl == i)
        if len(ys) < MIN_AREA:
            continue
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        if max(y1 - y0, x1 - x0) < MIN_SIDE:
            continue

        body_sub = (lbl[y0:y1, x0:x1] == i)
        ink_sub = ink[y0:y1, x0:x1] & body_sub
        soft = inkness[y0:y1, x0:x1]

        name = f"{sheet}_{kept:02d}"
        for pname, pmask in split(name, body_sub):
            save_fish(pname, pmask, ink_sub & pmask, soft, records)
        kept += 1
    return kept


def split(name, body):
    """One blob usually means one fish, unless SPLITS says otherwise."""
    rect = SPLITS.get(name + ".png")
    if not rect:
        return [(name + ".png", body)]
    h, w = body.shape
    xa, ya, xb, yb = rect
    sel = np.zeros_like(body)
    sel[int(ya * h):int(yb * h), int(xa * w):int(xb * w)] = True
    return [(name + "a.png", body & sel), (name + "b.png", body & ~sel)]


def save_fish(name, body, ink_sub, soft, records):
    if not body.any():
        return
    ys, xs = np.nonzero(body)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    body = body[y0:y1, x0:x1]
    ink_sub = ink_sub[y0:y1, x0:x1]
    soft = soft[y0:y1, x0:x1]

    eye = find_eye(ink_sub, body)
    angle = ANGLE_FIX.get(name, orientation(body, eye))

    # alpha: solid body, plus the anti-aliased ink so lines stay smooth.
    # Outside the body only strong ink survives, so scan shadows and
    # paper texture don't leave a grey halo around the fish.
    edge = np.clip((soft - INK_LO) / (INK_HI - INK_LO), 0, 1)
    edge = edge * edge * (3 - 2 * edge)          # smoothstep
    # a neighbouring fish can overlap this fish's bounding box, so only
    # keep soft edges hugging this body
    near = ndimage.binary_dilation(body, disk(3))
    alpha = np.where(body, 1.0, edge * near).astype(np.float32)
    # colour: white paper inside, original grey for the ink strokes
    rgb = np.clip(1.0 - (soft - 0.08) / 0.72, 0, 1)

    h, w = alpha.shape
    out = np.zeros((h + 2 * PAD, w + 2 * PAD, 4), dtype=np.uint8)
    out[:, :, :3] = 255
    for ch in range(3):
        out[PAD:PAD + h, PAD:PAD + w, ch] = (rgb * 255).astype(np.uint8)
    out[PAD:PAD + h, PAD:PAD + w, 3] = (alpha * 255).astype(np.uint8)

    # saved unrotated, so the drawing keeps its own tilt and facing
    fish = Image.fromarray(out, "RGBA")
    fish = fish.crop(fish.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox())

    fish.save(os.path.join(OUT, name))
    records.append({
        "file": name,
        "w": fish.width,
        "h": fish.height,
        "angle": round(angle, 2),
        "eye": eye is not None,
    })


def main():
    os.makedirs(OUT, exist_ok=True)
    records = []
    for f in sorted(os.listdir(SRC)):
        if not f.lower().endswith(".png"):
            continue
        sheet = f.split()[-1].split(".")[0]
        print(f"{f}: {process(os.path.join(SRC, f), sheet, records)} fish")
    with open(os.path.join(OUT, "manifest.json"), "w") as fh:
        json.dump(records, fh, indent=1)
    print(f"total {len(records)}, with eye found: {sum(r['eye'] for r in records)}")


if __name__ == "__main__":
    main()
