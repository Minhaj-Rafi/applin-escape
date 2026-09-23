# Android preview — nearby co-op

- Added landscape touch controls, Android-private save storage and pause-on-background behavior.
- Added authoritative two-device co-op over the same Wi-Fi with automatic discovery and a four-digit lobby code.
- Added paired-device Bluetooth RFCOMM co-op with Android Nearby Devices permissions.
- Added compressed game-state synchronization so enemies, timers, pickups, biome mechanics and shiny states remain identical on both phones.
- Added readable connection, rejection and disconnect states; a host run pauses if Player 2 disconnects.
- Added Buildozer packaging, a GitHub APK workflow, Android privacy notes, a two-phone test checklist and six automated mobile/network tests.

# 5.3.1 — Challenge sharing fix

- Challenge entry now opens with an empty, focused input field.
- The latest generated code remains saved and can be restored later.
- Added mouse selection, Ctrl+A, Ctrl+C, Ctrl+V, cursor navigation and editing.
- Added visible Paste, Copy selected and Show latest code actions.
- Added release notes and stronger Windows candidate packaging checks.
- Packaging now rejects missing screens, duplicate captures and untested window sizes.
- Added a multiresolution Windows application icon.
- Added Windows file-version and product metadata for the executable Properties dialog.
- Added GitHub issue/PR templates, privacy, support, security, contribution,
  conduct, licensing, third-party notice and release-checklist documents.
- GitHub Actions can now create a version-checked draft release from the browser.

# 5.3 — Controller release candidate

- Replaced event-dependent controller actions with safe state polling.
- Added fallback mappings for DualSense devices not recognized by SDL GameController.
- Added button-edge handling, reconnect/disconnect detection and a live input tester.
- Prevented plugged-in hardware from contaminating automated Windows build tests.
- Retained keyboard-only recovery for the known Pygame event conversion fault.

# 5.2.1 — Windows build and sanctuary fixes

- Close SQLite backup and restore connections explicitly before renaming files, fixing the reported WinError 32.
- Isolate the controller lifetime unit test from physical devices already connected to the build PC.
- Remove Adventure setup from the sanctuary sidebar.
- Show “not required” for zero resident requirements; clarify completed deliveries.
- Verify existing shiny odds, independent co-op rolls and run-only persistence.

# 5.2 — Homeward release candidate

- Biome-specific orchard rows, wetland junctions, shrine courts, ruin rings and highland terraces.
- AE52 code version; AE42/AE31/AE3 layout compatibility retained.
- Refined original cutscene bird artwork with throat, crest and wing details.
- Versioned native Windows ZIP packaging, checksum and release instructions.
- Windows workflow builds a candidate artifact without publishing automatically.

# Earlier release notes

# Applin Escape v5.0 — Better Together

New optional paired beacons appear in fresh modern co-op runs (AE42 rules).
P1 stands on the gold pedestal numbered 1; P2 stands on the blue pedestal numbered
2. Hold both positions for 1.5 seconds of gameplay. Leaving a position or having
P2 down resets an unfinished hold. Once lit, beacons remain complete for that run.
Finish at the shrine to bank a permanent team stamp for the biome. All five stamps
earn the Partner badge shown in Adventure setup > Team journal.

Click a pedestal to pause and read the team instructions. The live header shows
hold progress. The objective is optional: it never blocks the shrine and grants
no extra score, escape charges or gameplay upgrades. Base maps, collectibles and
random-number sequences are unchanged. Spawn selection uses an independent seed.
If a map cannot provide suitable distinct locations, beacons are omitted.

Old saved expeditions retain their original objectives; new saves preserve beacon
positions and progress. Solo, tutorial and legacy AE3/AE31 runs have no beacons.
The existing Windows input recovery, keyboard-only launcher, setup check and
support-report tools remain available.

Extract into a fresh folder and run PLAY_WINDOWS.bat; confirm HOMEWARD 5.0.
Actual Windows/controller validation remains outstanding; checks here ran on Linux.

## Previous releases and guide

# Applin Escape v4.9 — Run Insights & Support

Records > Run insights shows personal per-biome results for Standard, Expert or
Relaxed, separately for solo and co-op. It includes completed attempts, clear rate,
average successful-clear time and average hits per completed attempt. Tutorials,
abandoned attempts and older rows lacking difficulty/player details are excluded.
Runs from different versions, abilities and non-tutorial modes are combined; these
are descriptive personal totals, not controlled difficulty benchmarks. Guidance
requires at least five completed attempts in a biome. No automatic difficulty changes.

Settings > Troubleshooting displays version, sound/controller status and a save
integrity check. Export support report writes exports/support_report.json in the
save folder. It includes technical status only, without aliases, paths, save data
or raw crash logs. Nothing is uploaded automatically.

Close the game and run CHECK_SETUP.bat to test window/input startup and render one
map in each biome. It uses a temporary progress database and writes only a report
to exports/setup_check.json in your normal save folder. Audio/controller status is
reported; a pass does not verify physical buttons, speakers or extended gameplay.
The existing keyboard-only launcher and event error recovery remain included.

Extract into a fresh folder and run PLAY_WINDOWS.bat; confirm HOMEWARD 4.9.
Your existing save is retained. Native Windows and physical controller playtesting
remain outstanding; the automated checks here ran under Linux.

## Previous releases and guide

# Applin Escape v4.8 — Residents at Home

Open Garden & residents > Resident album > Meet & requests.
Each resident has one of five personalities, a stable favourite berry, and rotating
original dialogue. Share one berry prefers the favourite when available and still
adds only one friendship heart. At three hearts, ordinary gifts do not spend berries.

Each resident has three saved requests: a greeting, a two-berry favourite picnic,
and reaching three hearts after harvesting their favourite variety. Complete them
in order to earn that resident's Home ribbon, displayed in their profile. Requests
never expire and already-completed requests cannot consume berries again. The
picnic is a request delivery, separate from ordinary friendship gifts. Ribbons are
resident profile badges, not gameplay upgrades or shiny-style unlocks.

In the walkable sanctuary, select Preview decorations. Browse all nine decorations,
including locked rewards, with their requirements. Apply only changes an unlocked
selection; browsing leaves your current garden unchanged.

All existing progress is retained. Existing greetings, hearts and harvested varieties
count toward requests; request completions and new dialogue history begin in v4.8.
The 4.7.1 event-error recovery and PLAY_KEYBOARD_ONLY.bat workaround are included.
Extract into a fresh folder, launch PLAY_WINDOWS.bat and confirm HOMEWARD 4.8.

## Previous releases and guide

# Applin Escape v4.7.1 — Windows input hotfix

This patch addresses the reported KeyError: 0 followed by SystemError in
pygame.event.get(). The signature matches upstream Pygame event-conversion reports;
the exact triggering hardware has not been reproduced here.

The game blocks unused raw joystick events and continues using SDL controller
input normally. If the specific error still occurs, it switches to keyboard/mouse,
pauses and saves the active expedition, and displays a notice on the main menu.
Unrelated or repeated event errors still produce a crash report.

Extract this release into a fresh folder. Run PLAY_WINDOWS.bat normally.
For an explicit keyboard/mouse-only workaround, run PLAY_KEYBOARD_ONLY.bat.
Both launchers use the same existing save location. No Python upgrade or save reset
is required. Verify the launch banner says HOMEWARD 4.7.1.

Upstream report: https://github.com/pygame/pygame/issues/4568

## Earlier releases and game guide

# Applin Escape v4.7 — A Clearer Journey

- Blocked swoops stop and recover rather than stepping outside the warned route.
  This fixes modern biome rules; legacy AE3 behaviour remains unchanged.
- Capture results identify the bird and whether it was swooping.
- Existing open clearings gain subtle biome-specific ground accents. This is a
  readability pass, not a replacement map generator; movement and shared map
  layouts are unchanged.
- Sanctuary square > Sanctuary guide opens four optional, player-paced pages.
  Close anytime and replay it whenever you like. Illustrations stay still.
- Garden actions and project deliveries report newly earned achievement counts,
  home milestones and decoration unlocks in the existing notice area.

Validation: 129 automated tests, including a 50-map sample across five biomes
checking objective reachability with shortcuts closed and safe spawn distances.
Native Windows and physical-controller testing still need actual devices.
Existing saves are preserved. Extract into a fresh folder and run PLAY_WINDOWS.bat;
the launch banner should show HOMEWARD 4.7.

## Previous releases and guide

# Applin Escape v4.6 — A Thriving Home

Home milestones expand from 4 to 16. Sanctuary achievements expand from 72 to 96,
with a separate Advanced mastery category. Existing 72 goals and their profile
rewards keep their original requirements; previous progress is preserved.

New: six repeatable community projects, found under Garden & residents > Projects.
Projects require specific berry varieties and, later, rescued/happy residents.
Deliveries spend the listed berries only after all requirements are met. They
have no deadlines. Three different projects unlock Market stall, all six unlock
Welcome gazebo, and all 24 advanced goals unlock Sanctuary monument. Choose the
unlocked decoration in the sanctuary. The celebration acknowledges full mastery.

Advanced goals require balanced harvests across all four varieties, watered and
natural cultivation, three different ripe beds together, varied project deliveries,
larger resident communities, and successful rescues in all biomes. Expert rescue
requires both Budew; careful rescue requires both Budew and zero hits in tier 4 or
5 on Standard or Expert. Tutorial runs never advance rescue mastery.

Achievement browsing has Gardening, Community and Advanced mastery filters, an
unfinished-only option, mouse-wheel/Page Up/Page Down support, and row selection
to pin a goal in Sanctuary square. Growing timers and run-only shiny odds stay as
before. You never need to leave the game open for crops to grow.

Existing totals count where recorded. New mixed-bed, project and detailed rescue
tracking begins with v4.6; old saves did not retain these events. No save reset.
Extract into a fresh folder and launch PLAY_WINDOWS.bat; check HOMEWARD 4.6.

## Previous releases and guide

# Applin Escape v4.5 — Life at Home

This update fixes overlapping main-menu buttons, removes the stretched sanctuary illustration,
and aligns story characters by their feet. The selected bed's growth message updates live,
including its transition to ready-to-harvest.

Sanctuary now has 72 stamps: the original 36 gardening stamps plus 36 goals covering Budew
rescues, distinct residents greeted, happy residents, biome restoration, interaction days,
best daily streaks, berries shared, berry varieties and combined rescue/gardening/friendship.
Daily streak milestones are 3, 5, 7 and 14 local calendar days. Planting, watering, harvesting,
talking and successful berry gifts count as interactions. Opening a menu or leaving it idle
does not count. Missing a day resets only the current streak; your best remains recorded.
No need to leave the game running. Crops still grow offline and never spoil.

Existing saves, stamps, Garden crown and its celebration remain available. Home companion
unlocks at 54 stamps and Sanctuary guardian at all 72, with an expanded celebration message.
Existing recorded rescues, friendships and restored biomes count immediately. Interaction-day
and berry-gift tracking begins in v4.5 because earlier saves did not record those histories.

Extract this ZIP into a fresh folder and run applin_escape/PLAY_WINDOWS.bat.
The launch banner must say HOMEWARD 4.5. Default saves stay in the existing save location.

## Earlier release notes and game guide

# Applin Escape — Homeward (v4.4)

An offline 2D maze adventure built with Python and Pygame. Lead Applin through five outdoor biomes, collect sun seeds, rescue optional Budew, outwit flying pursuers and reach the animated sanctuary. Play alone or with a second player on the same keyboard.

This upgrade builds on v4.3 and preserves the existing gameplay and local history. Full-map view remains the default. Predator names, chase counts, the seed progress bar, distinct gold seeds and blue berries, original music, and the unlabeled shrine remain.

![Wetland co-op](previews/tier_2.png)

## New in v4.4: Two Journeys

- Sanctuary square now has just **Garden & residents** (the existing nursery, resident and decoration tabs) and **Sanctuary achievements**. Duplicate shortcuts, records/profile and maze contracts are removed from this hub.
- **Maze challenges** has its own main-menu button. Each of the 960 combinations earns an individual permanent mastery stamp. Collection rows identify earned stamps.
- Maze reward thresholds are **1, 10, 50, 120, 240 and 960** stamps: Copper trail, Silver trail, Gold trail, Sapphire trail, Star trail and Master crown. Equip a title/frame in Rewards, then export your player card to use it.
- Sanctuary has **36 separate garden stamps**: four berry varieties × three methods (any harvest, watered, natural/unwatered) × milestones of 1, 3 and 6 harvests. Counts accumulate automatically when harvesting. An any-harvest stamp can overlap a watered/natural stamp. These never advance maze mastery.
- Sanctuary rewards unlock at **1, 12, 24 and 36** stamps: Seed ribbon, Flower ribbon, Orchard ribbon and Garden crown profile frames/titles.
- Each complete collection unlocks its own replayable illustrated celebration in its Rewards screen: **The master explorer returns** for maze mastery, and **The garden festival** for sanctuary care. Rewards are cosmetic and never affect shiny odds or gameplay.
- Cutscenes use an original horizontal flying-bird sprite with hinged wings and no standing feet/shadow. Applin stays planted rather than sliding side to side. Comfort mode remains static.

Existing maze mastery immediately qualifies for the appropriate rewards. Harvest-method history was not recorded before v4.4, so the new garden stamps start counting from this update; crops, inventory, friendship and existing decorations are preserved. Completion-preview images use isolated demonstration progress, not a player-facing unlock shortcut.

## Previous update: v4.3 Sanctuary Seasons

**Home sanctuary → Sanctuary square** organizes six destinations: berry nursery, resident lodge, milestone board, challenge hall, records and player profile. You can also walk to the cottage entrance and press Interact.

### Timed berry growing

| Variety | Normal growth | Appearance |
| --- | --- | --- |
| Oran | 2 minutes | Blue round berry |
| Pecha | 5 minutes | Pink pointed berry |
| Cheri | 10 minutes | Paired red berries |
| Sitrus | 15 minutes | Yellow oval berry |

Choose the variety with the Plant selector before planting an empty bed. Water once to subtract 20% of the original growth time. Repeated watering cannot speed it up further. Deadlines persist and progress while the app is closed. Ripe berries never spoil. Existing ripe v4.2 crops stay ripe; unfinished older crops migrate to an Oran timer. Timers use the computer's wall clock.

### Challenge collection

The hall offers **960 combinations**: 5 biomes × 3 difficulties × 4 abilities × 2 player modes × 8 goals. Goals cover a normal clear plus every combination of no hits, rescuing both Budew and using no escape charges. A successful maze clear only earns mastery when its selected conditions are satisfied. Browse all combinations, see completed entries and select any entry to load it into the hall.

Mastery titles unlock at 1, 10, 50, 120, 240 and 960 distinct completed combinations. Repeating an already completed combination improves its clear count/time but does not add another collection entry. Progress has no daily reset. AC1 codes preserve a contract's goal and underlying AE42/AE31/AE3 challenge. Standard map codes remain supported.

### Records, player name and sharing

Records now page through the complete history using the mouse wheel, Page Up/Down or buttons. In Name & sharing, enter an alias up to 20 characters and save it. Export creates `player_card.png` and `player_card.txt` in `%LOCALAPPDATA%\ApplinEscape\exports`, with your name, local summary, contract count and last challenge code. Share the files yourself. This is not an online account, identity verification or an online leaderboard.

### Animated scenes

Story scenes now add local Applin movement, bird wingbeats and wetland ripples. The landscape and camera remain fixed. Comfort mode holds the scene still. Save backups, recovery, co-op signals and previous improvements remain included.

## Previous update: v4.2 Clear Trails

### More sanctuary activities

Open **Home sanctuary → Sanctuary square → Berry nursery**.

- Three berry beds: plant, water twice, then harvest two berries. v4.3 replaces instant growth with the timers described above.
- A paginated resident album includes every rescued Budew. Talk once to earn a first friendship heart, then share garden berries to reach three hearts. Talking to nearby residents in the walkable garden also counts.
- Home milestones unlock **Picnic** (one harvest and three total friendship hearts) and **Blossom arch** (five harvests and five total hearts). Choose them with the sanctuary decoration button.
- Gardening, berry inventory, friendships and milestones are saved automatically. These berries are separate from maze collectibles and do not change abilities, difficulty or shiny odds.

### Adventure polish

- **Inspect landmarks:** click fruit, tide, bell, wheel or wind tiles to pause and see their use, availability and real cooldown. Keyboard/controller users can use Pause → Inspect nearest landmark. Return to the pause menu and resume when ready. Nearby hints also show live cooldowns.
- **Six-part safe tutorial:** movement, grass, fruit distraction, escape, seed and shrine. A dotted route points toward lesson targets. Tutorial health remains protected and escape charges refill.
- **Tactical difficulty progression:** in new Standard/Expert runs, one interceptor in tier 3 and two in tiers 4–5 aim ahead toward corridors/junctions. Other birds keep their species roles. Relaxed keeps the gentler targeting. Distractions remain effective. New runs use AE42 challenge codes; AE31 and AE3 replays keep their original rules. Existing saved runs retain their rules version. Balance still needs human playtesting.
- **Readable predators and poses:** persistent shape cues supplement status colours. Applin has movement tilt, alert marks and escape compression; swooping birds bank. Comfort mode disables these animated poses.
- **Story payoffs:** each cleared stage offers a Chapter ending button with a short illustrated scene and rescue-dependent dialogue. The last ending reports your saved sanctuary totals. Rescue messages include a short Budew response.
- **Co-op calls:** F3 calls from P1, F4 from P2; buttons also appear above the map. On a mapped controller, Back/Select calls from that controller's player when it is not rebound to an ability. Numbered flags last five gameplay seconds. A downed partner has a map box and a rescue countdown.
- **Results:** seeds, rescued Budew, berries, elapsed time, steps, escapes, score and comparison with prior best time/steps for the same rules category. Different generated mazes are not identical courses; treat the comparison as personal progress, not a controlled speedrun.
- **Accessibility:** Settings → Sound / readable text offers independent music/effect levels and larger wrapped reading text for stories, notices and object details. It does not globally enlarge the dense gameplay HUD. Fullscreen and comfort settings remain available.
- **Recovery:** three rotating SQLite backups are made on launch and clean close. Close the game, run RESTORE_SAVE.bat and select a backup to restore. Recovery validates the backup and preserves previous database files in a dated folder. This cannot recover progress that was never saved. Crash reports now include version, time and platform information.
- **Windows build gate:** BUILD_WINDOWS.bat now runs the test suite before packaging. The GitHub Actions workflow also tests, builds and checks assets on Windows when you run it in your repository. No native Windows executable is included in this source ZIP; native Windows and physical-controller testing remain pending.

## New in v4.1

- Fixed the crash when inspecting a restored sanctuary garden. All five gardens are checked through mouse, keyboard and simulated controller input, both before and after restoration.
- Fifteen illustrated story panels across the five biomes, with layered landscapes, trees, stepping stones, ruins and a starry highland. Advance or revisit scenes at your own pace, or choose Begin chapter immediately.
- Restored gardens now offer a Story memories button. Revisit their scenes without changing your active run, save, progress or shiny rolls.
- Added fixed garden texture, orchard trees and cottage roof details. Comfort mode holds every story frame still; gentle local character/leaf motion is available when comfort mode is off.
- Existing v4.0 saves and run-only shiny appearances are preserved. This is a graphics/story update; it does not change maze rules or difficulty.

![Illustrated story](previews/story.png)

## Start on Windows

1. Extract **the entire ZIP** into a new folder.
2. Open its `applin_escape` folder.
3. Double-click **PLAY_WINDOWS.bat**.
4. Select **Tutorial**, **Story expedition**, or **Adventure setup** to choose your ability, rules and player count. Open **Home sanctuary** to visit your garden.

Python 3.10 or newer is needed for the source package. The launcher creates a private environment and installs Pygame on first use; internet is needed for that setup only. The actual game is offline.

If launching in PowerShell, first enter the extracted game folder containing `main.py` and `requirements.txt`:

```powershell
cd "C:\path\to\applin_escape"
py -m pip install -r requirements.txt
py launch.py
```

No need to delete the older version. The game keeps its existing local map history and previous results. New achievements are earned in v3.0; they are not inferred from old runs.

## Homeward update (v4.0)

### Clear biome landmarks

All five mechanics now use larger landmarks with distinct silhouettes and consistent iconography. They remain recognizable on the full map, with a minimum landmark size and contrasting highlights, shadows and physical supports. Seeds and berries render above nearby landmark details, so these additions do not hide collectibles.

| Mechanic | What to look for |
|---|---|
| Fruit lure | Three large red fruits hanging from a branch with an ivory-marked post |
| Tidal crossing | Broad ivory stones between coral-tipped posts; amber before closing; blue waves and a crossbar when flooded |
| Shrine bell | A filled golden bell with a wide lip beneath an indigo roof |
| Turning gates | A violet six-spoke wheel; ivory gate pillars marked I and II |
| Wind ride | A striped teal-and-orange windsock, plus bright feather-shaped marks showing direction |

Click the biome icon beside the map title, or open **How to play → Illustrated biome guide**, for the five illustrated explanations. A nearby keyboard hint shows the Interact binding. The objects do not require colour alone to distinguish them.

Gameplay integration checks exercise real input dispatch and the app update loop: fruit/bell activation redirects birds; the wheel swaps collision routes and refreshes scenery; the tide waits for a player occupying the crossing; wind activation moves three cells without consuming escape charges. These checks are included alongside the original rule and save tests.

### Rare shiny Applin, for one run only

Each active Applin has an independent **1 in 256** chance of starting a fresh run with a green shiny apple body. In co-op, neither, one, or both can be shiny. This demo's chosen probability is independent of official games' encounter rates.

- The roll uses system randomness, separately from the maze generator.
- Shiny is **not** an Apple style, unlock, purchase, setting or earned reward.
- It temporarily overrides the chosen body colour, with a small steady star and a HUD label. It gives no gameplay advantage.
- Normal campaign chapter changes preserve the roll across the expedition. Saving and continuing also preserve it.
- A retry or newly started adventure makes fresh rolls. The previous shiny colour does not carry into that new attempt.
- Challenge codes reproduce the maze and rules, **not** the shiny roll. Sharing or replaying a shiny run's code does not guarantee a shiny character.
- Older saves without shiny information resume with normal colours; loading them does not add a roll.
- The home garden and main menu show ordinary Applin. A rare appearance is never added to the permanent style list.

The preview named `shiny_example.png` is an illustration produced with a controlled test fixture. There is no corresponding player-facing force-shiny control.

### Five-chapter story expedition

**Story expedition** introduces an original story about recovering the sanctuary's scattered sun seeds and bringing its missing Budew home. Each chapter leads into one existing biome, with a short illustrated introduction and a concrete garden-restoration goal. Text waits for your input; there are no forced timed cutscenes.

1. The scattered light — Bramblebrook Orchard.
2. Across the returning tide — Tideglass Wetlands.
3. A bell beneath the leaves — Bellfern Shrine.
4. The turning stone — Copperleaf Ruins.
5. A home under the stars — Starfall Highlands.

Solo or co-op, the selected difficulty and ability, comfort controls, save/continue and the existing five-stage progression all remain available. **Adventure setup → Five-stage expedition** keeps the original expedition flow without the story passages.

### A walkable home sanctuary

Use movement controls to walk through the stationary garden. Interact beside a resident to hear a short line, or inspect/click a garden plot to see its restoration goal. The sanctuary is peaceful and does not advance an active maze's timer.

Clearing a non-tutorial biome restores its garden area. Budew rescued during a successful stage arrive at home. All new rescued Budew are counted; up to ten are drawn together to keep the garden readable. The same completed stage cannot be credited twice by loading its saved state.

- **Natural** decoration is available initially.
- Restore one garden to unlock **Lanterns**.
- Bring three Budew home to unlock **Flowers**.
- Restore all five gardens to unlock the **Fountain**.

Previously recorded biome victories restore their matching gardens during migration. Old versions did not store exact rescue totals, so historical rescue counts are not invented. New story chapter completions are tracked from v4.0 onward. No sanctuary decoration changes shiny odds or character abilities.

## Living Biomes update (v3.1)

| Biome | New interaction | How to use it |
|---|---|---|
| Orchard | Falling fruit lure | Interact beside a fruit tree. After a short drop warning, nearby birds investigate for five seconds. Each tree rests for 14 seconds. |
| Wetlands | Tidal stepping stones | The optional crossing opens for 10 seconds per 16-second cycle. The last two seconds turn amber. It waits for occupants to leave before closing. |
| Shrine | Brass bells | Interact beside a bell to draw nearby birds toward it for six seconds. Each bell rests for 14 seconds. |
| Ruins | Turning shortcut gates | Interact beside the wheel. After a 1.5-second preview, one gate closes and the other opens. An occupied gate waits before closing. |
| Highlands | Wind lanes | Interact on a marked lane for a shielded three-tile wind ride. Quick Dash reaches up to six tiles when aligned with the wind. |

The Interact key defaults to **E for P1** and **Right Ctrl for P2**. New markers are drawn into the biome: fruit trees, bell posts, stepping stones, gate pillars and feather-like wind arrows. The top HUD explains the biome interaction, and the bottom line offers a control hint when no notice is active.

These mechanics create optional routes and distractions. They do not delete original maze corridors, so every required objective remains reachable. The ruin mechanism swaps two marked shortcut gates; it does not rotate the entire map. In the wetlands, the tide replaces the old switch-controlled bridge. In the ruins, the wheel replaces it. Other biomes retain the original timed bridge switch and ledge.

Birds now get longer warning windows in Standard and Relaxed, plus extra warning in the highlands. Standard and Relaxed allow at most one committed swoop at once; Expert allows two. Other birds may still patrol or chase normally. Swoops have a brief recovery, and a P1 respawn clears pending attacks. This is deliberate timing, not hidden automatic difficulty adjustment.

### Keyboard and controller setup

Open **Settings → Controls / gamepads**. Click a movement, ability or interaction binding and press its replacement key. Conflicting bindings are rejected; Esc cancels. Shared menu shortcuts stay reserved. Reset bindings restores the defaults.

SDL-mapped gamepads support left stick / D-pad movement, **A (south) for ability**, **X (west) for interaction**, and **Start for pause**. In menus, D-pad moves focus, A confirms and B returns. Ability and interaction buttons can be rebound. Choose which co-op player uses the first pad; a second pad uses the other player. Stick deadzone can be 20%, 30% or 40%. Disconnecting a controller pauses gameplay.

Unsupported/unmapped joysticks are not treated as if they had a known layout. Input logic is tested using simulated devices; physical-controller testing is still pending. Implementation follows the [Pygame SDL controller API](https://www.pygame.org/docs/ref/sdl2_controller.html).

### Existing saves and challenge codes

The v4.0 gameplay generator still uses **AE31** codes; v4.0 adds presentation, story and run cosmetics without changing those map rules. **AE3** codes continue to generate v3.0 challenges with their original terrain and pursuit timings. An existing v3.0 active save resumes under its legacy rules; newly generated stages use v3.1. Existing map history, records, achievements and settings remain. New personal bests are separated by rules version as well as the existing mode settings.

## New adventures

- **Four selectable abilities.** Leaf Slip hops to a safer corridor with a decoy, nearby stun and short shield. Quick Dash travels up to four straight corridor tiles with a brief shield. Decoy Apple distracts birds for seven seconds. Camouflage prevents detection of P1 and contact damage for five seconds; in co-op birds can still pursue the visible partner. All abilities use the same limited charge pool and cooldown. Wind rides have a separate two-second cooldown and do not spend charges. Berries slow birds; they do not refill charges.
- **Three challenge settings across five biomes.** Relaxed adds a heart, two charges and slower birds. Standard strengthens ordinary pursuit. Expert increases speed further. Difficulty does not secretly adjust during a run.
- **Telegraphed swoops.** Gold circles mark a bird's committed route. A warning sound and exclamation precede its accelerated flight. Change route during the warning; the swoop does not home in after commitment. All bird movement follows walkable corridors.
- **Optional rescue routes.** Walk over each twig-enclosed Budew for 350 points. Both rescues plus a stage win unlock Blossom style. Rescues are not required to unlock the shrine.
- **Interactive shortcuts.** In the orchard, shrine and highlands, walk onto the teal diamond switch to open a bridge shortcut for 12 seconds. A bridge stays open until everyone leaves its tile. White arrows mark one-way ledges: press E at the tail to jump to the other side. Shortcuts are optional; the underlying maze stays connected.
- **A final pursuit.** Collecting the last seed announces a three-second warning, after which the flock pursues more aggressively. The shrine is immediately available; its opening animation does not hold you back.
- **Playable tutorial.** Practice movement, grass concealment, abilities, seeds and escape without losing health. Tutorial charges refill, and tutorial wins do not award normal cosmetics or personal bests.
- **Local co-op.** P1 uses WASD and P2 uses arrows. Seeds, score and escape charges are shared. P1 being caught costs a shared heart and resets the flock; P2 becomes temporarily downed. P1 can touch P2 to rescue them, or P2 recovers at the nest after eight seconds. Both apples must reach the shrine. Running out of shared hearts ends the attempt.

## Controls

| Action | Solo / Player 1 | Player 2 in co-op |
|---|---|---|
| Move | WASD; arrows also work in solo | Arrow keys |
| Escape ability | Space | Right Shift |
| One-way ledge | E | Right Ctrl |
| Pause/resume | P / Esc | Shared |
| Full map / optional quiet camera | V | Shared |
| Trail | T | Shared |
| Music | M | Shared |
| Field guide | F1 | Shared |
| Fullscreen | F11 | Shared |
| Menu keyboard navigation | Tab then Enter | Shared |

Some keyboards cannot register many simultaneous keys. If a co-op input does not register, try another keyboard. Controller support is available through Settings. Online multiplayer is not part of this version.

## Saving and continuing

The game saves every three seconds while playing, on focus loss, and when closing normally. **Pause → Save & return to menu** gives an explicit save. Choose **Continue saved** to restore the map, collected items, birds, timers, random state, rules and expedition results. A cleared expedition stage is also saved so you can return later and continue to the next biome.

There is one active save slot. Starting a new adventure or challenge replaces that slot. **Abandon attempt** records an abandoned result; it does not create a resumable save. If the process is forcibly killed, up to the last three seconds of progress can be lost.

Windows saves: `%LOCALAPPDATA%\ApplinEscape\progress.sqlite3`. Copy the save folder while the game is closed to back it up. Graphics and audio assets are never written into that folder. Crash reports from the launcher are written to `last_error.txt` there.

## Journal, achievements and cosmetics

**Adventure setup → Collection journal** contains illustrated bird entries, biome stamps, six achievements and personal bests. Best time, fewest steps and no-hit completions are tracked separately by biome, difficulty, ability, solo/co-op and game mode. Challenge records also include the challenge code. Best time and fewest steps can come from different runs; the visible list shows the nine most recently inserted rule categories.

| Style | How to unlock | Appearance |
|---|---|---|
| Orchard | Available from the beginning | Original apple |
| Golden | Clear a non-tutorial stage | Golden body, warm trail and shrine leaves |
| Moonleaf | Clear without a hit | Blue apple, cool trail and shrine leaves |
| Blossom | Rescue both Budew and clear | Pink apple, flower accessory, pink trail and shrine leaves |

P2 uses a blue palette and numbered marker to remain distinguishable. Styles have no gameplay bonuses.

## Shareable challenges and map history

Use **Share challenge** on the pause or result screen. The full `AE31-...` code (or `AE3-...` for a legacy game) is shown, copied to the clipboard when supported, and written to `challenge_code.txt` in the save folder. A friend enters it through **Adventure setup → Challenge code**. The code fixes the biome, random seed, challenge setting, ability and player count. Shiny rolls remain independent. It restarts the adventure from the beginning rather than copying your current progress.

Normal adventures reject previously generated base maze layouts, including their rotations and reflections, using persistent local history. Clearing or moving that history resets the guarantee; separate computers have separate histories. Challenge mode deliberately permits repeat maps and does not consume a normal-history entry. Codes are versioned: AE31 for v3.1 and AE3 for legacy v3.0 rules. Matching codes guarantee matching initial maps and objectives, not matching outcomes after different inputs.

## Animation, graphics and sound

- Recognizable original bird palettes, crests and wingbeats; north/south flight views and horizontal flight views; lowered stunned poses and searching hover.
- Applin eye glances toward nearby birds, periodic blinks, small seed celebrations and unlockable appearances.
- Local grass disturbances, optional collection particles, gently animated rescue creatures, seed/berry details and shrine opening.
- Five original biome compositions and a menu theme; warning and rescue sounds; biome-specific quiet pursuit rhythms fade in with danger.
- Separate music, sound effects, adaptive music, particles, character animation, scenery animation and trail settings. Scenery animation defaults off.
- Comfort Mode fixes the full map and stops decorative and character animation. Gameplay positions still change. No camera shake, screen flashes or strobing effects are added.

The optional quiet camera is available with V when Comfort Mode is off. It uses a stationary central zone and follows only when the player approaches an edge. Full-map mode remains the default for every new or resumed stage.

## Landscapes and original tracks

| Stage | Biome | Track | Broad visual influence |
|---|---|---|---|
| 1 | Bramblebrook Orchard | Bramblebrook Morning | Bright early handheld outdoor routes |
| 2 | Tideglass Wetlands | Tideglass Crossing | Coastal exploration and wooden crossings |
| 3 | Bellfern Shrine | Bells Beneath the Ferns | Woodland paths and shrine paving |
| 4 | Copperleaf Ruins | Copperleaf Footsteps | Autumn routes and weathered ruins |
| 5 | Starfall Highlands | A Sky Full of Waypoints | Rocky highlands and open skies |

Pidgeotto tracks, Cramorant guards objectives, Spearow ambushes ahead, Murkrow alternates pursuit and roaming, and Talonflame is a faster tracker. These are fan-game behavior assignments, not claims that every listed species canonically preys on Applin.

All maps, drawings and music in this package were created for this project. No official game maps, sprite rips, recordings or transcribed themes are included. This is an unofficial Pokémon fan project, not affiliated with or endorsed by the Pokémon rights holders.

## Build a Windows executable

The package contains **build support, not a precompiled Windows EXE**. On Windows, double-click **BUILD_WINDOWS.bat**. It installs the pinned build requirements into a separate environment, runs a bundled-asset smoke check, and builds `dist\ApplinEscape\ApplinEscape.exe`.

Share **the entire `dist\ApplinEscape` folder**, including `_internal`, as a ZIP. Players using that built version do not need Python. The source package still uses the Python launcher above.

The included `.github/workflows/windows-build.yml` provides a manually started Windows build with tests, bundled-asset preview checks and a downloadable artifact. It has not been run or published to your GitHub repository. Add all source files and folders at your repository root, including `.github`, before using it. The workflow only uploads a build artifact; it does not create a public release.

Build approach follows [PyInstaller operating-mode documentation](https://pyinstaller.org/en/stable/operating-mode.html) and [spec-file documentation](https://pyinstaller.org/en/stable/spec-files.html). Windows builds must be produced on Windows. This development pass built and smoke-tested the frozen application on Linux, including bundled audio and controller imports. A Windows executable and physical-controller playtest still need the included Windows build and actual hardware.

## Development and verification

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python main.py --preview previews --verify-build
```

For a machine without a display/audio device, set `SDL_VIDEODRIVER=dummy` and `SDL_AUDIODRIVER=dummy` before running tests. The suite also covers independent shiny rolls, save continuity, all five story chapters, home progression, landmark contrast, input-driven biome interactions, timed tides, occupied ruin gates, legacy migration, input remapping, controller actions and disconnects. Human playtesting is still needed for difficulty and keyboard feel.

Audio is already included. Rebuild original base effects with `python audio.py`, biome music with `python compose.py`, and the new warning/rescue/pursuit sounds with `python compose_expansion.py`.

Source layout: `home_progress.py` contains rare-roll and restoration rules; `sanctuary.py` draws the home and story; `story_art.py` renders the illustrated landscapes; `biome_art.py` draws the new landmarks. `model.py` contains the original rules and persistence; `expedition.py` extends them; `biome_rules.py` and `biome_ui.py` add v3.1 terrain; `controls.py` handles keyboard/gamepad input; `main.py` runs the app; `adventure_ui.py` contains the new screens and illustrations; `art.py` and `world.py` draw the sprites and scenery. `launch.py` is the desktop launcher.
