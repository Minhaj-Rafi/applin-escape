# Android preview verification

## Automated checks

- 168 tests pass: the original 162 game/release tests plus 6 Android and nearby-network tests.
- Wi-Fi lobby authentication accepts the correct four-digit code and rejects an incorrect code.
- Host-to-guest and guest-to-host messages were exercised through real loopback TCP sockets.
- A complete tier-three co-op session snapshot was compressed, transferred and restored with matching stage ID, player position, enemy positions and shiny state.
- Nearby discovery, code-entry and lobby screens render without overlapping buttons.
- Touch movement press, hold state and release are covered.
- Existing Windows controls, procedural maps, five biome mechanics, sanctuary, challenges, saves, shiny odds and packaging tests remain green.

## Visual checks

The nearby selection screen, lobby-code keypad, Player 2 waiting room and touch
gameplay overlay were rendered at the game's 1280×840 logical resolution and
reviewed together in `android-preview/contact-sheet.png`.

## Toolchain status

Buildozer 1.6.0 accepted the project configuration and reached the Android host
requirements check. This workspace does not contain a Java compiler, Android SDK
or Android NDK, so it cannot produce the APK locally. The included GitHub Actions
workflow installs OpenJDK 17 and the official Buildozer prerequisites before
building the APK.

## Still required before a public Android release

An APK must be built and installed on two physical Android phones. Complete the
Wi-Fi, hotspot, Bluetooth, permission-denial, screen-background, disconnect,
sound, save and long-play checks listed in `ANDROID_RELEASE.md`. Automated desktop
tests cannot validate radio hardware, Android permission dialogs or touch comfort.
