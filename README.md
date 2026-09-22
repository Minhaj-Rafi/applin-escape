# Applin Escape 5.3.1 — Player guide

An unofficial Python/Pygame maze adventure with five biomes, solo play and local
co-op. Artwork and music are original procedural assets. No online account or
online multiplayer is included.

## Start on Windows

1. Extract the entire ZIP into a new folder. Do not launch inside the ZIP.
2. Open `applin_escape` and double-click `PLAY_WINDOWS.bat`.
3. Check that the banner says **HOMEWARD 5.3.1**.

Python 3.10+ is required for this source package. The launcher creates its own
Python environment and installs Pygame on first launch. Later launches can work
offline. If controller startup causes trouble, use `PLAY_KEYBOARD_ONLY.bat`.
`CHECK_SETUP.bat` checks startup and all five biome renders using temporary progress.

## The adventure

Collect every gold sun seed to activate the shrine, then reach it safely.
Rescuing Budew is optional; successful rescues bring residents to your sanctuary.
Birds fly along maze paths. Their warnings show committed swoop routes; blocked
modern swoops stop and recover. Full-map viewing is the default.

Start with Playable tutorial in Adventure setup. Choose Relaxed, Standard or
Expert, then one of Leaf Slip, Quick Dash, Decoy Apple or Camouflage. Escape
charges are limited. Fruit lures, tidal crossings, bells, turning gates and wind
lanes create tactical options. Click a landmark to pause and inspect its rules.

| Default control | Action |
| --- | --- |
| WASD | P1 movement |
| Arrow keys | P2 movement in co-op; movement in solo |
| Space / Right Shift | P1 / P2 escape |
| E / Right Ctrl | P1 / P2 interact |
| P or Escape | Pause during a run |
| F3 / F4 | P1 / P2 call marker when available |
| Tab + Enter | Menu navigation |
| F11 | Fullscreen |

Controls can be remapped. Gamepads use D-pad/left stick for movement, the south
face button for escape, the west face button for interaction and Options/Start for
pause. Version 5.3 polls controller state instead of depending on the Windows event
queue and includes an unmapped DualSense USB/Bluetooth fallback. Settings > Controls
shows the controller name and a live input-test line.

## Local co-op

Both players use the same computer. New modern co-op runs may include numbered
beacons. P1 holds 1 and P2 holds 2 for 1.5 seconds together; then finish the run to
bank a biome team stamp. Five stamps earn the Partner badge in Team journal.
This objective is optional and does not change score, escape charges or shrine rules.
Earlier saved runs keep their original objectives.

## Your sanctuary

Enter Home sanctuary, then Sanctuary square. Garden & residents contains four tabs:

- **Berry garden:** three beds and four timed berry varieties. Water once for a
  20% reduction in original growth time. Crops grow offline and never spoil.
- **Resident album:** talk, share berries and open Meet & requests. Budew have
  personalities and favourite berries. Complete three requests to earn that
  resident's Home ribbon. Request delivery and friendship gifts are separate.
- **Home milestones:** 16 goals, including decoration unlocks.
- **Projects:** six repeatable community deliveries requiring specific varieties
  and resident support. Nothing is spent unless all requirements are met.

The Sanctuary guide is optional and replayable. Preview decorations in the walkable
sanctuary; only Apply changes an unlocked selection. Nine decoration choices exist.

Sanctuary achievements has **96 goals**, including **24 advanced mastery goals**.
Filter by category or unfinished goals, then select a row to pin it at home.
Original profile reward thresholds use the first 72 goals. Advanced mastery
unlocks the Sanctuary monument. A missed interaction day does not erase the best
streak or earned rewards. You never need to keep the game open for growth timers.

## Challenges, records and sharing

Maze challenges has 960 combinations of biome, difficulty, ability, player mode
and objective. Each completed combination receives a permanent stamp. Cosmetic
profile frames and titles unlock at milestones; collection celebrations can be
watched from Rewards. These are separate from sanctuary goals.

Records includes paginated runs, a local player name, exportable share cards and
Run insights. Insights combines recorded versions and modes within each difficulty
and player mode; use it as personal history, not a controlled balance benchmark.
Reports and share cards are local files. Nothing is uploaded automatically.

AE52 challenge codes use new biome route patterns; older codes preserve their maps.
Challenge codes replay a map; normal generation rejects previously recorded
layouts on this computer, including mirrored/rotated copies. Uniqueness is local,
not a global guarantee across installations. Shiny Applin is a rare independent
run-only roll: 1 in 256 per player, independent in co-op. Both being shiny is
1 in 65,536. Continuing a save preserves the roll; a new run rolls again. Shiny
is never an Apple style or purchasable unlock.

The challenge-entry page opens with a blank field. Click the field to type, or
use Paste/Ctrl+V. Codes can be selected with click-drag or Ctrl+A and copied with
the Copy button or Ctrl+C. **Show latest code** retrieves your most recently
generated code even after leaving the share screen.

## Saves and updates

On Windows, default progress is in `%LOCALAPPDATA%\ApplinEscape`, outside the game
folder. Extract updates into a new folder and use their launcher. Do not delete
your save folder. Runs save periodically and when closed. Existing run-only shiny
state and team objective progress are saved with that expedition.

Three rotating save backups are maintained. Close the game before using
`RESTORE_SAVE.bat`; it asks which backup to restore and preserves replaced files.
Newer activity counters start when that feature is introduced; older events cannot
be reconstructed if an older version did not record them.

## Comfort and troubleshooting

Comfort Mode keeps the map fixed and turns off character animation. Reading size,
audio levels, effects and other presentation controls are in Settings.
Settings > Troubleshooting can export a small technical report. It omits aliases,
paths, save contents and raw crash logs. Crash details are separately written to
`last_error.txt` in the save folder.

## Build and release status

`BUILD_WINDOWS.bat` tests and builds a Windows distribution with PyInstaller, then
renders the release preview and creates a versioned ZIP plus SHA-256 checksum in
`release/`. That Windows build does not require players to install Python. A GitHub Actions workflow is
included for a repository whose root contains these game files.

This download contains source and assets, **not a verified Windows executable**.
See `WINDOWS_RELEASE.md` for build and publishing steps, `RELEASE_STATUS.md` for completed checks and remaining real-device playtests,
`TEST_REPORT.txt` for results, and `CHANGELOG.md` for earlier release notes.
