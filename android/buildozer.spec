[app]

# (str) Title of your application
title = AuRA

# (str) Package name
package.name = aura

# (str) Package domain (needed for android/ios packaging)
package.domain = org.auraengine

# (str) Source code where the main.py live
source.dir = .

# (str) Source files to include
source.include_exts = py,png,jpg,kv,atlas,json

# (str) Application versioning
version = 0.2.0

# (list) Application requirements
requirements = python3,kivy,numpy,scipy

# (str) Supported orientation
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
#icon.filename = %(source.dir)s/data/icon.png

# (list) Permissions
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE

# (int) Target Android API
android.api = 33

# (int) Minimum API your APK / AAB will support.
android.minapi = 26

# (str) Android NDK version to use
android.ndk = 25b

# (int) Android NDK API to use
android.ndk_api = 26

# (str) The Android arch to build for
android.archs = arm64-v8a

# (bool) Accept the Android SDK/NDK license
android.accept_sdk_license = True

# (str) The format used to package the app for release mode
android.release_artifact = apk

# (str) The format used to package the app for debug mode
android.debug_artifact = apk

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (str) Android logcat filters to use
android.logcat_filters = *:S python:D

# (bool) Android logcat only display log for activity's pid
android.logcat_pid_only = False

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
