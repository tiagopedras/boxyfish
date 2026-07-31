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

## Adding your own fish

The camera button at the bottom of the panel opens a modal with the webcam in
it. Hold a drawing inside the white bracket facing right, take the photo, and
it gets cut out the same way the scans were: background dropped, body filled,
paper thrown away. Whatever colour is inside the outline is kept, in both
themes, so a captured fish stands out from the 52 originals.

The feed is mirrored like a mirror, and the photo is mirrored to match, so
what you framed is what you get. Only the middle 80% — what the bracket
encloses — is used.

If it comes out swimming backwards, **Flip direction** mirrors it, with the
preview updating live. **Add to aquarium** drops it in from off-screen.

There is only ever one captured fish. It is always among the fish on screen,
and it stays until you capture another or reload the page — nothing is saved.

On a phone the modal skips the camera entirely and goes straight to uploading
a photo — the file picker there offers the camera anyway, and a live feed in a
modal is awkward one-handed. The panel's keyboard hint is hidden too, and
tapping the tank away from the panel hides it; tapping again brings it back.

With no webcam, or if camera access is refused, the modal offers to upload a
photo instead. Note that browsers only allow camera access on `localhost` or
over HTTPS, so a plain `http://` deployment will fall back to upload.

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

## Pointer

Move the pointer near a fish and it turns away from you and puts on a brief
burst of speed, settling back after about a second.

Press on a fish and you can drag it around. It hangs off the pointer near its
head, so the body trails behind, beats its tail hard, and tilts to point the
way it is being pulled. Let go and it bolts off.

A fish turning far enough to reverse is mirrored rather than rotated, so it
never ends up belly-up. Mirroring is deliberately reluctant — the direction
has to be decisively opposite and stay that way for a moment — because a fish
flickering between the two directions looks much worse than one briefly
swimming a little backwards. This matters most on a touchscreen, where a
wobbling finger would otherwise set it off.

## Colours

Every fish is stored as plain white-with-black-lines, and the theme decides
what those two become — so recolouring costs nothing and needs no new files.
To add a theme or change the palette, edit `THEMES` near the top of the script
in `index.html`; each entry is a background colour plus a list of body colours.
The outline of each fish is worked out automatically as a deep version of its
body colour.
