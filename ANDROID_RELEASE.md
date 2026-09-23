# Android preview build

The Android edition keeps the complete maze, sanctuary, challenge, save and
shiny systems. It adds a landscape touch interface and nearby two-device co-op.

## Build an APK on GitHub

1. Upload the complete repository, including `.github/workflows/android-build.yml`,
   `buildozer.spec`, `mobile_ui.py`, `mobile_platform.py`, `network_coop.py`, all
   tests and the complete `assets` folder.
2. Open **Actions** in GitHub.
3. Choose **Build Android game**.
4. Choose **Run workflow** and wait for both `test` and `apk` to become green.
5. Open the completed workflow and download **ApplinEscape-Android-Debug** from
   its Artifacts section.
6. Extract the artifact, transfer the APK to an Android phone, allow installation
   from that trusted source when Android asks, then install it.

The first GitHub build is slow because Buildozer downloads the Android SDK, NDK
and Python-for-Android toolchain. Later builds use the workflow cache.

## Mobile controls

- Use the four large arrow buttons to move.
- **USE** interacts with fruit branches, bells, turning wheels and wind lanes.
- **ESC** uses the selected escape ability.
- **II** pauses. The Android Back button also pauses or returns.
- The game remains landscape and scales the same fixed logical canvas to phones
  and tablets without cropping gameplay.

## Two-device co-op on the same Wi-Fi

1. Connect both phones to the same Wi-Fi or phone hotspot.
2. On the host, open **Adventure setup > Nearby co-op > Host a Wi-Fi game**.
3. On Player 2's phone, open **Nearby co-op > Find Wi-Fi games**.
4. Select the host and enter the four-digit code shown on the host phone.
5. The host selects **Start two-device adventure**.

No Internet server or account is involved. The code is valid only while that
lobby is open. Some school or public Wi-Fi networks isolate devices; a personal
hotspot or Bluetooth is more reliable in that case.

## Two-device co-op over Bluetooth

1. Pair the two phones in Android Settings first.
2. Grant the game's **Nearby devices** permission on both phones.
3. On the host, choose **Host by Bluetooth**.
4. On Player 2's phone, choose **Paired devices**, select the host phone and enter
   the four-digit lobby code.
5. Start the adventure from the host.

The host is authoritative: it simulates birds, timers, pickups, biome mechanics,
score and the rare shiny rolls. Player 2 sends only input. Compressed snapshots
keep both displays synchronized and prevent the two devices from drifting.

## Required real-device checks

- Install and launch on at least two ARM64 Android phones.
- Accept and deny Nearby Devices once; denial must give a readable error.
- Complete one Wi-Fi run and one Bluetooth run.
- Turn a screen off briefly; the host must pause rather than continue unseen.
- Disconnect Player 2; the host must pause and report the disconnect.
- Verify sound, touch hold/repeat, USE, ESC, Back, sanctuary timers and save reload.

The workflow can verify source and produce an APK, but it cannot prove Bluetooth
radio behavior or touch comfort. Those checks require two physical phones.
