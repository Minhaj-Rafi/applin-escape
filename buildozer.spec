[app]
title = Applin Escape
package.name = applinescape
package.domain = io.github.minhajrafi
source.dir = .
source.include_exts = py,png,jpg,svg,wav,txt,md,json
source.exclude_dirs = .git,.github,.venv,venv,tests,previews,android-preview,build,dist,release,build-preview-frozen-final,build-preview-frozen-github,build-preview-frozen-release,build-preview-frozen-v51,build-preview-frozen-v52,build-preview-frozen-v53,build-preview-frozen-v53-final,build-preview-frozen-v531,build-preview-release,build-preview-v4,build-preview-v41,build-preview-v42,build-preview-v43,build-preview-v44,build-preview-v51,build-preview-v52,build-preview-v521,build-preview-v53,build-preview-v53-final,build-preview-v531,build-preview-v531-final
version = 5.3.1
requirements = python3,pygame==2.1.0,pyjnius,android
icon.filename = assets/app_icon_512.png
orientation = landscape
fullscreen = 1

android.permissions = android.permission.INTERNET,android.permission.ACCESS_NETWORK_STATE,android.permission.ACCESS_WIFI_STATE,android.permission.CHANGE_WIFI_MULTICAST_STATE,(name=android.permission.BLUETOOTH;maxSdkVersion=30),(name=android.permission.BLUETOOTH_ADMIN;maxSdkVersion=30),(name=android.permission.BLUETOOTH_SCAN;usesPermissionFlags=neverForLocation),android.permission.BLUETOOTH_CONNECT,android.permission.BLUETOOTH_ADVERTISE
android.api = 35
android.minapi = 26
android.ndk_api = 26
android.archs = arm64-v8a, armeabi-v7a
android.private_storage = True
android.accept_sdk_license = True
android.logcat_filters = python:D SDL:D *:S
android.copy_libs = 1

[buildozer]
log_level = 2
warn_on_root = 1
