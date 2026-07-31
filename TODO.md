# TODO

## Interactive version

Ideas parked for the `interactive` branch. All four are worth doing; they are
not mutually exclusive.

- **Fish react to the cursor** — fish notice the pointer as it moves, either
  shying away from it or curiously following it. Nothing to click; the tank
  just responds to movement.
- **Click to feed** — a click drops food, nearby fish break off and swim to it,
  then go back to what they were doing. The most aquarium-like of the four.
- **Click a fish** — clicking an individual fish makes it respond: dart away,
  turn to face you, or come forward. Aimed at one fish rather than the shoal.
- **Drag a fish around** — while a fish is being dragged with the mouse it
  beats its tail rapidly, and its body tilts to point along the direction it
  is being pulled. Let go and it swims off normally.
- **Click to add a fish** — each click drops another fish in, so someone can
  build up their own tank.

Open question when we start: whether this needs to work on touchscreens and
shared displays as well as a desktop mouse. That decides whether every
interaction needs a tap equivalent and whether hover can be relied on at all.

## Fixes to the current version

- **Confirm fish spawn outside the frame after the fish slider is adjusted.**
  They should swim in from off-screen, never appear mid-tank. Worth checking
  properly rather than by eye.
- **Change the starting defaults** to turning 0, speed 9, wave 1.3. Note the
  speed slider currently tops out at 2.5, so its range needs widening for 9 to
  be reachable.
- **Don't remove fish immediately when the fish slider is turned down.** Right
  now the least-visible fish is deleted straight away. Better to let the extra
  fish swim out of frame on their own and simply not replace them.
