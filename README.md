# Applin Escape — Sunseed Edition (v2.4)

A complete offline desktop maze-chase fan-game demo. Guide Applin through five scenic difficulty tiers while a mixed flock of autonomous bird Pokémon patrols and pursues it. Includes original code-drawn 2D fan sprites, animation, five original biome music tracks plus a menu theme, sound effects, local records, and persistent map-repeat prevention.


## Sunseed update (v2.4)

- The gold seed is now a pointed teardrop with a rounded body, warm shading and a central seam. The berry is round and cobalt blue, with violet shading, a pale highlight and a bright leafy crown. Their silhouettes and palettes differ without heavy badge outlines.
- Pickups retain a minimum display size on the full map. Gentle local highlights and leaf motion are controlled by Character animation; scenery remains stationary by default.
- Collection bursts now work with Character animation enabled, without requiring animated scenery.
- The enlarged shrine's double doors open over 1.1 seconds after the last seed is collected, revealing a softly lit interior and small rising motes. The animation freezes while paused. With animation disabled or Comfort Mode enabled, the open doorway is shown immediately. The visual transition does not delay the gameplay unlock.
- All five tiers have stronger pursuit: lower movement intervals, greater detection distances, shorter patrol phases and 14-second chase phases. Escape charges are now 3, 2, 2, 1 and 1.
- Full map remains the default, with predator names, chase count and the seed progress bar retained. No camera shake, strobe or screen flash is added.

Difficulty still needs human playtesting. Stop if visual discomfort occurs; use Character animation OFF or Comfort Mode to reduce local animation.

## Biome features retained

- Handheld-inspired outdoor maps with trees, dirt trails, tall grass, flowers, rocks, shrine paving, ruined walls, animated water and wooden bridges.
- Connected clearings change the layouts, giving Applin space to dodge. Every accepted layout is still checked against your history.
- An optional following camera uses larger tiles and characters. The stationary full map is the default; V switches to the optional camera when Comfort Mode is off. The HUD prioritizes the predator roster and collectible legend.
- Tall grass halves a bird's detection range, with a minimum range of three cells. It reduces detection, not collision damage or the need to keep moving.
- Five species with distinct custom sprites and assigned roles.
- Five original looping tracks, automatically selected by biome. Muting persists when the track changes.

### Landscapes and music

These are design inspirations for newly created work, not reconstructions of official maps or songs.

| Stage | Landscape | Broad inspiration | Original track | Arrangement |
| --- | --- | --- | --- | --- |
| 1 | Bramblebrook Orchard | Bright FireRed/LeafGreen-style outdoor routes | Bramblebrook Morning | Pulse lead, bass, light percussion; 112 BPM |
| 2 | Tideglass Wetlands | Ruby/Sapphire/Emerald-style coastal exploration | Tideglass Crossing | Marimba-like lead, bass and percussion; 126 BPM |
| 3 | Bellfern Shrine | SoulSilver-style woodland atmosphere | Bells Beneath the Ferns | Bells, spacious accompaniment; 90 BPM |
| 4 | Copperleaf Ruins | Black/White-style seasonal scenery | Copperleaf Footsteps | Reed-like lead, rhythmic bass and percussion; 136 BPM |
| 5 | Starfall Highlands | X/Y-style scenic highlands, reimagined in 2D | A Sky Full of Waypoints | Glassy lead, echoes and soft bass; 104 BPM |

Tracks are approximately 28–37 seconds each. All melodies, arrangements and PCM audio files were generated for this project. No official recordings or transcribed Pokémon themes are included.

### Bird roster by stage

| Stage | Gameplay pursuers |
| --- | --- |
| Breezy | Pidgeotto |
| Watchful | Cramorant, Spearow |
| Daring | Murkrow, Pidgeotto, Spearow |
| Relentless | Talonflame, Murkrow, Pidgeotto, Cramorant |
| Apex | Talonflame, Murkrow, Spearow, Pidgeotto, Cramorant |

These species are selected as opponents for this fan game's scenario. This roster is **not a verified list of species canonically documented as preying on Applin**. The official Pokédex pages could not be read during verification, so no species-specific claim is made here.

### Updating from the previous demo

Extract the new ZIP into a fresh folder and run its `PLAY_WINDOWS.bat`. Close the old game first. The same local save database is used automatically, so your map history, settings and journal remain available. The new folder may install its own private environment on first launch.

## START HERE — Windows

1. Extract **the entire ZIP** using **Extract All**. Do not run from inside the ZIP viewer.
2. Open the extracted `applin_escape` folder.
3. Double-click **PLAY_WINDOWS.bat**.

The launcher opens its own folder automatically, finds Python, creates a private `.venv` environment, installs Pygame on first launch, and opens the game. Python 3.10–3.12 is recommended; Python 3.10 is supported. Internet is needed only for first-time dependency installation. Later launches work offline. If setup fails, the launcher leaves the error visible.

Already have Pygame? Manual launch from PowerShell works too:

```powershell
cd "C:\Users\NUHAN\Downloads\Applin_Escape_Advanced\applin_escape"
py -m pip install -r requirements.txt
py main.py
```

That example assumes the ZIP was extracted into `Applin_Escape_Advanced` in Downloads. If your folder name differs, open the folder containing `main.py`, type `powershell` into File Explorer's address bar, then run the last two commands.

On Linux/macOS, open a terminal in the game folder, create a virtual environment with `python3 -m venv .venv`, activate it with `source .venv/bin/activate`, then run `python -m pip install -r requirements.txt` and `python main.py`.

## Your mission

Collect every **gold sun seed** and reach the **sanctuary gate**. The wooden shrine doorway lights up when unlocked. Small dew drops are optional score pickups. Blue chill berries slow the flock for six seconds.

The stationary full map is the default. Press **V** for the optional camera, or use Comfort Mode to lock the full map and disable character animation. Use loops to evade birds instead of retreating into dead ends. A red dot above a pursuer signals pursuit; a gold dot means it is stunned. A green ring around Applin is a temporary safety shield.

### Modes

- **Five-stage expedition:** progress through all five tiers. Hearts and escape charges reset for each stage. A failed stage can be retried on a fresh map; already-cleared stages remain completed in the current expedition.
- **Practice:** choose any tier immediately. Every attempt creates a fresh maze.
- **Journal:** recent results and best cleared-stage score, saved locally.

This is a single-player desktop demo. There is no online multiplayer or mid-attempt resume after closing the application. Settings, map history and completed/abandoned attempt records persist. Expedition progression lasts for the current application session.

## Five distinct difficulty tiers

| Tier | Environment | Maze cells | Pursuers | Base bird step interval | Leaf Slips | Hearts | Sun seeds | Detection distance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Breezy | Bramblebrook Orchard | 21 × 17 | 1 | 0.28 s | 3 | 3 | 3 | 12 cells |
| Watchful | Tideglass Wetlands | 25 × 19 | 2 | 0.23 s | 2 | 3 | 4 | 16 cells |
| Daring | Bellfern Shrine | 29 × 21 | 3 | 0.19 s | 2 | 3 | 5 | 20 cells |
| Relentless | Copperleaf Ruins | 33 × 23 | 4 | 0.17 s | 1 | 2 | 6 | 24 cells |
| Apex | Starfall Highlands | 37 × 25 | 5 | 0.155 s | 1 | 2 | 7 | 30 cells |

Detection uses walkable path distance. Individual birds have small speed offsets; Talonflame receives an additional 10% reduction in its movement interval. Applin moves once every 0.135 seconds while a movement key is held. Later tiers have shorter patrol breaks as well as larger maps and greater pursuit range. These are initial balance values; human playtesting can guide further tuning.

## Controls

| Input | Action |
| --- | --- |
| WASD / arrow keys | Move; hold to keep moving |
| Space | Use a limited Leaf Slip escape |
| P / Escape | Pause; Escape resumes from pause |
| Enter | Start expedition, resume, or select the main result action |
| 1–5 in the menu | Select a practice tier |
| T | Toggle visited-corridor trail |
| V | Switch views only with Comfort Mode OFF; stationary map otherwise |
| M | Toggle music |
| F1 during play | Pause and open the field guide |
| F11 | Toggle fullscreen |
| Tab, then Enter | Focus and activate menu buttons |
| Mouse | Use menus and on-screen buttons |

Resize the window freely; the game maintains its proportions. Losing window focus automatically pauses gameplay. Music may continue while paused and can be muted independently. Settings also allow disabling sound effects and reducing animation.

## Leaf Slip: your limited escape move

Press **Space** before a bird catches you.

1. Search the maze graph for a floor cell 5–14 walking steps away and at least five walking steps from a bird.
2. Prefer the safest available candidate. If necessary, widen the search and require at least three steps of separation.
3. Teleport Applin there without crossing through walls as an ordinary move.
4. Leave a decoy for 3.5 seconds, stun nearby birds for 2 seconds, and grant a 2-second shield.
5. Consume one charge and apply a 1.5-second cooldown.

Charges never refill within the stage. If there is no acceptable destination, the charge is preserved. Leaf Slip is tracked separately from walking steps. It is a custom ability for this game, not a claim about official Pokémon move rules.

## Pursuer AI

Every bird follows legal corridors and alternates between patrol and pursuit:

- **Pidgeotto / Talonflame — Tracker:** heads toward Applin's current cell. Talonflame moves slightly faster.
- **Spearow — Ambusher:** targets up to four cells ahead of Applin's movement direction.
- **Cramorant — Warden:** guards a remaining sun seed or the exit, switching to direct pursuit when close.
- **Murkrow — Roamer:** mixes direct pursuit with its roaming target.

Birds use breadth-first search to find shortest routes. They follow a decoy during its lifetime and slow down after a chill berry is collected. Neighbor reservation and alternate steps reduce birds blocking each other indefinitely.

## How map repetition is prevented

Randomized depth-first search builds a connected maze. A braiding pass removes most dead ends and creates escape loops. Connected clearings add room to dodge; terrain then creates paths, tall grass, water crossings and landmarks. Objectives are spread across the maze, the exit is far from the starting nest, and birds initially spawn at least 16 path steps away.

Before a layout is accepted, the game:

1. Normalizes rotations and reflections to a canonical representation.
2. Checks the entire canonical layout and its SHA-256 fingerprint against the local SQLite history.
3. Saves an unseen layout transactionally; if it already exists, generates another.

**No previously accepted layout is presented again while this computer's history is retained**, even if it is mirrored or rotated. This is a local guarantee, not a claim that finite grids have infinite unique possibilities. Deleting/resetting the save database, using a different save directory, or playing on another computer removes that shared history. After 256 unsuccessful candidates, the game reports an error instead of knowingly presenting a repeat. A maze reserved before a crash may remain in history without having been played.

## Measurements and scoring

The HUD shows active gameplay time, successful walking steps, hearts, sun seeds, remaining escapes, score, dew collected, and hits. Pause/help/settings time does not count. Escapes are measured separately; blocked movements do not add steps.

- Dew: **10 points** each.
- Sun seed: **500 points** each.
- Chill berry: **75 points** each.
- Cleared-stage bonus: `max(0, 1800 - floor(seconds) × 3) + hearts × 250 + unused escapes × 150`.

The end screen and journal show time, steps, escapes used and score. Campaign victory totals the five successful stages; failed attempts remain in the journal but are not part of that victory total. Leaving an active attempt records it as abandoned. The clock measures simulated active gameplay time; on an extremely slow machine, simulation is capped per frame rather than jumping ahead.

## Saves and privacy

Windows save location:

```text
%LOCALAPPDATA%\ApplinEscape\progress.sqlite3
```

Linux/macOS default: `~/.local/share/ApplinEscape/progress.sqlite3`.

Save state uses Python's built-in SQLite module. Back up the save folder with the game closed if you want to preserve your history. No account, telemetry or in-game network requests are used. `python main.py --save-dir PATH` selects a separate profile.

## Files and customization

| File | Purpose |
| --- | --- |
| `main.py` | Game loop, input, menus, scaling, animation and HUD |
| `model.py` | Difficulty settings, maze generation, AI, collision, escape logic, scoring and saves |
| `art.py` | Original procedural character sprites and icons |
| `audio.py` | Sound-effects synthesizer and runtime audio manager |
| `compose.py` | Five original multi-part biome compositions |
| `world.py` | Scenic terrain renderer, water, bridges, trees, ruins and shrine gates |
| `assets/audio/` | Included original WAV music and effects |
| `PLAY_WINDOWS.bat` | Windows setup and launch helper |
| `tests/` | Automated rule, persistence, audio and interface checks |
| `previews/` | Screenshots of the menu, guide and five tiers |

Change the five `TIERS` entries in `model.py` to tune difficulty. Maze dimensions must be odd and large enough for the configured collectibles and enemies. The supplied five configurations are tested; arbitrary custom dimensions are not validated. `art.py` sprites are drawn on transparent surfaces and cached at the required display sizes. No external images or fonts are required.

To regenerate sound assets, run `python audio.py` for effects/menu music and `python compose.py` for all five biome tracks. To produce new screenshots without affecting your save, run `python main.py --preview previews`.

## Verification

Run from the game folder:

```text
python -m unittest discover -s tests -v
```

The delivered version passed 30 automated tests, including 100 unique connected maps, objective reachability, safe spawns, mirror/rotation duplicate rejection across database reopen, escape charges and safe destinations, collision/respawn, five-stage progression, legal enemy movement, focus-loss pause, audio asset decoding, all-screen rendering, visible terrain/collision agreement, grass detection reduction, camera bounds, distinct pursuer sprites, five distinct music files with stage switching, fixed Comfort Mode camera, static decorative frames, low-motion defaults, quiet-zone stability, accurate pursuit/stun/decoy counts, full-map defaults on every stage, flight animation isolated from collision positions, revised difficulty parameters, distinct pickup shapes and colours, and shrine animation progression/pause behavior.

Testing was performed on Linux with Python 3.12 and Pygame 2.6.1 using SDL's headless video/audio drivers. Menu, gameplay and guide screenshots were visually inspected. The Windows batch launcher was reviewed but not executed on a Windows host; audible playback and human difficulty balancing still need testing on your device.

## Troubleshooting

- **Can't find `main.py` or `requirements.txt`:** use `PLAY_WINDOWS.bat` after extracting the entire ZIP. It changes to its own folder automatically.
- **Pygame installation fails:** use Python 3.10, 3.11 or 3.12 and check internet access. Other Python versions may need a compatible binary wheel or build tools.
- **No sound:** check Windows volume/mixer and the game's Settings. Audio failures do not stop gameplay.
- **Small characters at Apex:** maximize the window if comfortable. Keep Comfort Mode enabled if scrolling caused discomfort.
- **Cannot save:** check that your user profile's save directory is writable and that the drive has free space. Preserve the database when troubleshooting if you want repeat prevention to remain intact.
- **Window appears stuck:** use Alt+Tab to give it focus, then Enter or Escape to resume from pause.

## Credits

Unofficial, noncommercial fan-game demo. Pokémon and the named species belong to their respective owners. This project uses newly drawn stylized fan sprites and newly synthesized music/effects; it does not include official game sprites, logos, music or recordings. Not affiliated with or endorsed by the Pokémon rights holders.
