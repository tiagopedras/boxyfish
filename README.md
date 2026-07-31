# Aquarium

Hand-drawn fish swimming across a white screen. The fish come from the scanned
sheets in `src/`, cut out one by one and animated in 3D.

## Run it

The page has to be served, not opened by double-clicking — browsers block a
local page from reading its own image files.

```bash
python3 -m http.server 8123
```

Then open http://localhost:8123

## The panel

Bottom right, fades out when the mouse stops. Press **H** to hide it entirely.

| Control | What it does |
|---|---|
| Theme | **Paper** — white background, black-line fish. **Water** — blue background, fish in assorted blues, purples and oranges |
| Fish | How many are on screen at once (default 8) |
| Speed | How fast they swim |
| Wave | How much the body ripples |
| Turning | How far they swing towards and away from you |

## Re-cutting the fish

`assets/fish/` already holds 52 cut-out fish, so you only need this if you add
new scans to `src/`.

```bash
python3 -m venv .venv && .venv/bin/pip install numpy pillow scipy
.venv/bin/python tools/extract_fish.py
```

The script finds each fish, fills its body white and makes everything outside
the outline transparent. Each cut-out is saved **exactly as drawn** — same
proportions, same slight tilt, facing the same way — so nothing gets
straightened or flipped. It only works out which way each fish points, using
the eye dot as the head marker, and records that in the manifest.

Two things at the top of the script may need a hand:

- **`ANGLE_FIX`** — if a fish ends up pointing the wrong way (boxy bodies with
  a central eye are the tricky ones), give it a heading in degrees clockwise
  from "pointing right", e.g. `"8_05.png": 0.0`. Six fish currently need this.
- **`SPLITS`** — two drawings close enough on the paper to be treated as one
  fish. Give a rectangle, in fractions of the joined shape's box, marking the
  second fish; the pieces are saved as `…a.png` and `…b.png`.

## How the motion works

Each fish is a flat sheet cut into a fine grid. A wave travels down it from
nose to tail, pushing the grid towards and away from the viewer — so the body
undulates through depth rather than just wobbling on the flat. The wave runs
along the axis the fish was drawn on, so a fish sketched slightly tilted
ripples along its own tilt.

Each fish also slowly swings its heading, which turns it through the scene and
lets perspective foreshorten it. Fish nearer the camera are drawn bigger and,
since their bodies are solid white, they cover the fish behind them.

Sizes are a straight scale from the drawings, so a fish sketched twice as big
really is twice as big on screen. A fish swims in the direction it was drawn
facing, along the tilt it was drawn at, and leaves by whichever edge it reaches
— then it is recycled as a different fish entering from somewhere else.

## Colours

Every fish is stored as plain white-with-black-lines, and the theme decides
what those two become — so recolouring costs nothing and needs no new files.
To add a theme or change the palette, edit `THEMES` near the top of the script
in `index.html`; each entry is a background colour plus a list of body colours.
The outline of each fish is worked out automatically as a deep version of its
body colour.
