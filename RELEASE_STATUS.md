# Applin Escape 5.3.1 — Release candidate

This is a playable source release candidate. A verified Windows executable is not
included: the current build environment is Linux and no Windows runner is connected.

## Completed

- Five biome-specific regional route patterns with connected maze corridors.
- New AE52 codes; older challenge codes retain original layouts and rules.
- Refined original bird illustration; fixed scene aspect ratios and comfort controls.
- Existing Windows event recovery, keyboard fallback and controller lifetime fixes.
- Versioned Windows ZIP and SHA-256 packaging through BUILD_WINDOWS.bat or GitHub Actions.
- Player guide, Windows release instructions, changelog and refreshed screenshots.
- 162 automated tests passed, including controller polling, unmapped DualSense,
  disconnect handling and 60 generated-map connectivity/replay cases.
- Controller and joystick events are excluded from the fragile Python event queue;
  movement and buttons use safe polling with one action per press.
- Automated tests ignore physical devices attached to the build computer.
- Settings > Controls reports the device name and live input test.
- Challenge entry starts blank while the latest generated code remains retrievable.
- Challenge codes support mouse selection, keyboard selection, copy and paste.
- Packaging rejects incomplete previews and includes release notes in Windows builds.
- Windows builds use a multiresolution application icon.
- GitHub community documents, templates and browser-driven draft releases are prepared.
- 5.3.1 source and frozen Linux previews passed: 52 captures, three window sizes
  and bundled asset verification.
- The 5.3.1 PyInstaller Linux build completed successfully.
- Fixed reported backup file locking and physical-device interference in the build test.

## Included gameplay

Five biomes; three difficulty settings; four escape abilities; solo/local co-op;
biome interactions; story and reward scenes; rare run-only shiny appearances;
save backups; timed gardening; resident requests; community projects; 16 home
milestones; 96 sanctuary goals; 960 maze contracts; optional team beacons; local
share cards; comfort settings; run insights and support diagnostics.

## Remaining release gates

1. Build and launch the native Windows candidate, including on a PC without Python.
2. Test a physical DualSense over USB and Bluetooth, including disconnection,
   reconnection and local co-op.
3. Retest the Windows device that reported KeyError: 0 in pygame.event.get().
4. Complete a new-player walkthrough and comfort check, then review difficulty feedback.
5. Complete a name, character, music, artwork and distribution-rights review before
   any public or commercial release involving third-party properties.

Follow WINDOWS_RELEASE.md. These external gates are not passed by Linux tests.
Do not label the candidate a stable Windows release until those checks pass.
Online multiplayer, global leaderboards, automatic updating and professional
asset replacement are not part of this release scope. No publication has occurred.
