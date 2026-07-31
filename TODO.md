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
- **Dart away after a drag.** When a fish is released, it should swim away from
  the pointer at speed for about two seconds before settling back to normal.

## Webcam and preview modal

- **More padding on mobile.** The modal is currently cropped and some
  information is cut off. (Easiest to spot with the tank set to blue.)
- **Replace the black webcam rectangle with a placeholder** — dashed border with
  a fish outline centred, mimicking the shape of the preview.
- **Match the aquarium's waving defaults.** The fish in the preview should use
  the same wave settings as the fish in the tank.
- **Swap flip for rotate 90° clockwise.** Label the right edge of the preview
  frame "FRONT", rotated 90° clockwise and sitting next to the frame edge; do
  the same on the back.

## Options menu

- ~~**Move it behind a floating button.** A gear FAB in the bottom right opens
  the options menu, so the menu isn't in the way while playing with the fish.
  Add a close option inside the menu.~~ Done. The camera button moved out of
  the menu into its own FAB beside the gear.
