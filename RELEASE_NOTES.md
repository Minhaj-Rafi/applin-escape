# Applin Escape 5.3.1 — Challenge Sharing Fix

Applin Escape is an unofficial, locally played maze-adventure demo. This release
candidate combines five procedural biomes, solo and local co-op play, sanctuary
progression, timed gardening, resident activities, story scenes and challenge codes.

## Highlights

- Every normal run produces a fresh connected maze while challenge codes reproduce
  the same maze and rules for another player.
- Five biomes have distinct route structures, music, hazards and interactions.
- Solo and local co-op support keyboard and compatible game controllers.
- Rare shiny Applin colours are decided independently for each player per run and
  are not selectable or permanently unlocked.
- Comfort Mode reduces motion, flashing and screen effects.

## Fixed in 5.3.1

- Opening Challenge code entry directly now starts with a blank, focused field.
- A newly shared challenge code stays visible and is selected automatically.
- Players can click or drag to select a code and use Ctrl+A, Ctrl+C and Ctrl+V.
- Paste, Copy selected and Show latest code buttons provide mouse-only alternatives.
- The latest generated code remains recoverable and is also written to
  `challenge_code.txt` in the local save folder.
- Windows release builds now include a dedicated multiresolution application icon.

## Candidate status

The source, tests and frozen Linux smoke build have been verified. A native Windows
candidate must still be built and tested on Windows, including USB/Bluetooth
DualSense input and the previously affected event-queue device. See
`WINDOWS_RELEASE.md` and `WINDOWS_PLAYTEST.md` before calling the build stable.

This project is an unofficial fan-made demonstration. Public distribution still
requires a separate review of names, characters, artwork, audio and other rights.
