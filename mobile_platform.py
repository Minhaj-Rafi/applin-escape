"""Small Android compatibility helpers; harmless on desktop."""
import os
from pathlib import Path


def is_android():
    return "ANDROID_ARGUMENT" in os.environ or os.environ.get("APPLIN_MOBILE_TEST") == "1"


def android_save_dir():
    if not is_android():
        return None
    try:
        from jnius import autoclass
        activity = autoclass("org.kivy.android.PythonActivity").mActivity
        return Path(str(activity.getFilesDir().getAbsolutePath())) / "ApplinEscape"
    except Exception:
        return Path(os.environ.get("ANDROID_PRIVATE", Path.home())) / "ApplinEscape"


def request_nearby_permissions():
    """Ask only for runtime permissions used by nearby play."""
    if not is_android():
        return
    try:
        from android.permissions import request_permissions
        request_permissions(["android.permission.BLUETOOTH_SCAN",
                             "android.permission.BLUETOOTH_CONNECT",
                             "android.permission.BLUETOOTH_ADVERTISE"])
    except Exception:
        # Android versions below 12 grant legacy Bluetooth permissions at install.
        pass


def set_android_clipboard(value):
    if not is_android():
        return False
    try:
        from jnius import autoclass
        activity = autoclass("org.kivy.android.PythonActivity").mActivity
        context = autoclass("android.content.Context")
        clip_data = autoclass("android.content.ClipData")
        manager = activity.getSystemService(context.CLIPBOARD_SERVICE)
        manager.setPrimaryClip(clip_data.newPlainText("Applin Escape challenge", value))
        return True
    except Exception:
        return False


def get_android_clipboard():
    if not is_android():
        return ""
    try:
        from jnius import autoclass
        activity = autoclass("org.kivy.android.PythonActivity").mActivity
        context = autoclass("android.content.Context")
        manager = activity.getSystemService(context.CLIPBOARD_SERVICE)
        clip = manager.getPrimaryClip()
        if clip and clip.getItemCount():
            return str(clip.getItemAt(0).coerceToText(activity))
    except Exception:
        pass
    return ""
