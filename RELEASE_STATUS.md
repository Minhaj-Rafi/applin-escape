# Applin Escape 5.1 — Release checklist

## Completed in this release pass

- Shared version source for the game window, menu, crash report and support export.
- Retained joystick wrapper lifetime while a controller is active; safe cleanup if
  a controller disappears while it is being queried.
- Existing Windows input-error recovery and keyboard-only launcher preserved.
- Expanded release preview from the older screen subset to 51 captures, including
  all story panels, residents, decoration previews, team play, support and insights.
- Source and Linux packaged previews completed at 800x600, 1280x720 and 1600x900.
- 149 automated tests passed.
- PyInstaller Linux build succeeded; packaged audio/controller loading and all
  release previews succeeded. This does not constitute a Windows test.
- Windows build script and repository-root GitHub workflow check newer screen outputs.
- Consolidated player guide, earlier release notes and updated screenshots.

## Existing playable feature set

Five biome maze adventure; three difficulty settings; four escape abilities; solo
and local co-op; warnings and biome interactions; story and completion scenes;
run-only shiny rolls; save backups; timed gardening; resident requests; community
projects; 16 home milestones; 96 sanctuary goals; 960 maze contracts; optional team
beacons; share-card export; comfort controls; run insights and support diagnostics.

## Still requires real-world validation

1. Build and run on native Windows, including a PC without Python for the packaged build.
2. Test actual controllers: connect, disconnect, reconnect, and test local co-op.
3. Confirm the originally reported event-queue crash no longer occurs on the affected device.
4. Have new players try the tutorial, maze and sanctuary without coaching. Record
   unclear controls, missed objects, failed routes and any visual discomfort.
5. Review real completed-run data before making further difficulty adjustments.

The project is not certified bug-free or finished for every possible feature idea.
There is no online multiplayer, global leaderboard, automatic updater, or included
verified Windows executable. Major topology redesign and professional sprite/scene
production are future scope; the current map work adds clearing readability and
validates connectivity while retaining compatible generated layouts.

## Five-minute feedback form

Record game version, Windows version, input device, selected biome/difficulty,
what you tried, what happened, and what you expected. Include a screenshot when
helpful. Use Settings > Troubleshooting to export a small support report if needed.
Never send a save or raw crash log without checking it for information you prefer
not to share. No reports are sent automatically.
