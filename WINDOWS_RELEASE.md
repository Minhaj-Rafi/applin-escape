# Windows release candidate — 5.3.1

## Build on your Windows computer

Extract this source package and double-click BUILD_WINDOWS.bat. The builder needs
Python 3.10 or newer and internet access for dependencies. It runs the test suite,
builds the executable, checks bundled rendering/audio, and produces:

- release/ApplinEscape-5.3.1-Windows-RC.zip
- release/ApplinEscape-5.3.1-Windows-RC.sha256

Players extract the whole Windows ZIP and open ApplinEscape/ApplinEscape.exe.
They do not need Python. Keep the _internal directory beside the executable.
The source ZIP is different: its PLAY_WINDOWS.bat needs Python on first setup.

## Build using your GitHub repository

Upload the CONTENTS of applin_escape into the repository root, including the
.github/workflows/windows-build.yml file. If your browser skips the hidden .github
folder, create that exact file path using Add file > Create new file and paste its
contents. Open Actions, choose Build Windows game, and run the workflow on your
branch. Download its ApplinEscape-Windows-Release-Candidate artifact when all steps
pass. The artifact contains the Windows ZIP and checksum. Keep **Create a draft
GitHub release** disabled until native playtesting passes. Afterward, rerun with
that option enabled and tag `v5.3.1`; the workflow creates a draft for review.
See `GITHUB_RELEASE_GUIDE.md` for the complete browser-only process.

## Before calling it a stable Windows release

Run this exact packaged build on Windows, preferably also a computer without
Python. Confirm each item and record the machine/input device beside the result:

- Launch, hear music, change volume, enter each biome and inspect its mechanics.
- Play tutorial and a complete run; quit, reopen, and continue saved progress.
- Test keyboard and local co-op, pause, fullscreen and resizing.
- For each available controller: connect, disconnect during play, reconnect.
- In Settings > Controls, confirm the controller name appears and the INPUT TEST
  line responds to both sticks/D-pad and the face buttons.
- Retest the affected device that produced KeyError: 0 at pygame.event.get().
- Plant and water berries; check countdowns in all home views and after reopening.
- Open resident requests, achievements, records, celebrations and share export.
- Enable Comfort Mode and check that motion remains comfortable.

An automated preview cannot validate physical controller behavior or comfort.
Do not mark an unchecked item as passed. Keep RC in the download name until these
checks pass. If something fails, use Settings > Troubleshooting and report the
exact steps and version. No diagnostic information is sent automatically.

## Publish the tested candidate

Review the workflow-created draft, its tested Windows ZIP, checksum, release notes
and known issues before publishing. Retain the source ZIP for Python users.
The checksum detects accidental file changes; it is not a code-signing certificate.
The current executable is unsigned, so Windows may identify the publisher as
unknown. Do not disable system protection globally. A trusted code-signing
certificate is a separate future release requirement.
This project is an unofficial fan game, with original procedural art and music.
