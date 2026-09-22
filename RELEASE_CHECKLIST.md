# Release checklist — 5.3.1

## Automated gates

- [x] 162 automated tests pass.
- [x] All 52 release screens render with bundled assets.
- [x] 800×600, 1280×720 and 1600×900 window checks pass.
- [x] Linux frozen-build smoke check passes.
- [x] Incomplete previews and non-Windows executables are rejected by packaging.
- [x] Source ZIP integrity and required-file checks pass.

## Native Windows gates

- [ ] GitHub Actions `Build Windows game` workflow passes.
- [ ] Versioned Windows ZIP and SHA-256 file are downloaded and verified.
- [ ] `ApplinEscape.exe` launches on a Windows PC without Python.
- [ ] Keyboard tutorial and one full run pass.
- [ ] DualSense USB, Bluetooth, disconnect and reconnect pass.
- [ ] Local co-op passes with the intended input combination.
- [ ] Save, continue, backup and restore pass using disposable progress.
- [ ] Challenge-code select/copy/paste/reopen flow passes.
- [ ] All five biome mechanics, music and sanctuary timers pass.
- [ ] Comfort Mode and common window sizes receive a human visual check.

## Publication gates

- [ ] Release notes and screenshots are reviewed.
- [ ] Distribution rights and third-party naming/branding are reviewed.
- [ ] Draft GitHub release contains the Windows ZIP and checksum.
- [ ] If distributing beyond a small test group, decide whether trusted code signing is required.
- [ ] The draft is published only after every applicable gate above is recorded.
