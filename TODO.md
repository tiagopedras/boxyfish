# TODO

## Interactive version

Ideas parked for the `interactive` branch. All four are worth doing; they are
not mutually exclusive.

- **Click to feed** — a click drops food, nearby fish break off and swim to it,
  then go back to what they were doing.
- **Mobile and touch support** — the interactions currently assume a mouse.
  Every one of them needs a tap or touch-drag equivalent, hover can't be
  relied on at all, and a shared touch display may have several people
  touching at once.

Built on the `cursor` branch: fish shying away from the pointer, and dragging
a fish around by hand.

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
