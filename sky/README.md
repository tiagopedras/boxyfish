# Boxy Sky

Hand-drawn aeroplanes crossing a white sky, the ones high enough dragging a
vapour trail behind them. A fork of the aquarium one folder up: the same WebGL
renderer, flying instead of swimming.

## Run it

The page has to be served, not opened by double-clicking — browsers block a
local page from reading its own files.

```bash
python3 -m http.server 8123
```

Then open http://localhost:8123/sky/

## What's different from the aquarium

The fish came off scanned paper as PNG cut-outs. The aircraft are **SVG**, and
they were never on paper at all: `tools/draw_planes.py` describes each one as a
few straight-edged outlines seen from above and then walks those outlines with
a shaky hand, so every line wanders the way a drawn one does. The wobble is
seeded off the aircraft's name, so the drawings are the same every time the
script runs. The page rasterises each SVG into a texture at load.

There are eight: an airliner, a prop plane, a biplane, a delta jet, a paper
dart, a glider, a seaplane and a flying wing. Sizes are a straight scale from
the drawings, so the glider really is the long-winged one.

There is no options panel and no theme picker — one sky, white paper and black
ink — and the aircraft ignore the pointer. They are going somewhere.

## How the motion works

A fish undulates; an aeroplane holds a line. So the wave that ran nose-to-tail
down the fish is gone, and in its place:

- **Wings bend.** Nothing at the root, most of it at the tips, both sides
  together, plus a slower twist that lifts one tip against the other.
- **It banks into its turns.** Each aircraft picks a new course every few
  seconds and rolls towards it. The bank comes from the *rate* of the turn, not
  from how far it has turned, which is why the turn rate is capped — that cap
  is what keeps the banking from looking like a flick. Rolling shows the wings
  edge on, which is most of what makes these read as solid things.
- **It pitches.** Nose down when it is closing on the viewer, up when it is
  climbing away, taken straight from how fast its depth is changing.
- **It yaws through depth**, the way the fish did, so aircraft turn towards and
  away from you instead of sliding flat across.

Courses are shallow: a hand-drawn aeroplane standing on its wingtip stops
reading as one. Half of them fly the other way, with the drawing mirrored so
nothing is ever seen flying tail-first, and each leaves by whichever edge it is
pointing at before being recycled as a different aircraft coming in somewhere
else. Aircraft nearer the camera are drawn bigger and, being solid white, cover
the ones behind.

## Vapour trails

Only the airliner, the jet and the flying wing leave one — the propeller
aircraft and the glider are not up high enough, and a paper dart certainly
isn't.

A trail is a line of samples dropped behind the tail, drawn as a ribbon of
flat quads. Each sample carries two numbers that only matter once it has aged:
one drifts it sideways, the other decides when it thins out into a gap. So the
trail is a continuous line where it leaves the tail and a broken row of dashes
by the time it is five seconds old.

Both numbers are random walks rather than fresh draws each time, so
neighbouring samples agree with each other. Drawn independently the ribbon
zigzagged and every gap came out one sample long, which made the vapour look
like confetti.

Each trail is drawn immediately before its own aircraft, inside the same
far-to-near pass, so it goes behind its aeroplane and interleaves correctly
with everything else in the sky.

## Adding your own aeroplane

The camera button in the bottom right opens the same capture flow the aquarium
has, and it works the same way: hold a drawing inside the white bracket with
the nose to the right, take the photo, and it gets cut out — background
dropped, body filled, paper thrown away. Whatever colour is inside the outline
is kept. **Rotate 90°** turns it if you held it the wrong way up.

Your aeroplane gets a vapour trail whether or not you drew one, so you can
follow it. There is only ever one; it stays until you capture another or
reload, and nothing is saved.

On a phone the modal skips the live camera and goes straight to uploading a
photo. With no webcam, or if camera access is refused, it offers the same.
Browsers only allow camera access on `localhost` or over HTTPS.

## The link preview

Pasting the address into a chat window shows a card: the airliner with its
vapour still hanging behind it. The picture is `assets/og-sky.png`, and the
card it comes from is `../tools/og/sky.html` — serve the repo, open that page
at exactly 1200x630, screenshot it, and save it over the PNG. The vapour there
is drawn by hand in the card rather than taken from the page, so making it
again doesn't depend on catching the right frame.

`og:image` has to be an absolute URL, so the tags in `index.html` name the
deployment. If you host this somewhere else, that address needs changing.

## Redrawing the aircraft

`assets/planes/` already holds all eight, so you only need this to change them.

```bash
python3 sky/tools/draw_planes.py
```

No dependencies. Each aircraft is a list of outlines near the foot of the
script, nose pointing right along y = 0; `solid` shapes are filled with paper
white in the order given, so a wing listed before the fuselage tucks underneath
it, and `lines` are outline only — windows, creases, propeller discs. `SHAKE`
at the top sets how steady the hand is; 0 rules every line perfectly straight.
