[app]

# (str) Title of your application
title = Emaktab Auto

# (str) Package name
package.name = emaktabauto

# (str) Package domain (needed for android/ios packaging)
package.domain = com.emaktab.auto

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,txt

# (str) Application versioning (method 1)
version = 1.0

# (list) Application requirements
requirements = python3,kivy,requests,cryptography,pyjnius,android

# (str) Supported orientation (landscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
icon.filename = icon.png

# (list) Permissions
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# (str) Android logcat filters to use
android.logcat_filters = *:S python:D

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (str) Android entry point, default is ok for Kivy-based app
android.entrypoint = org.kivy.android.PythonActivity

# (str) Android app theme, default is ok for Kivy-based app
android.theme = "@android:style/Theme.NoTitleBar"

# (list) Android application meta-data to set (key=value format)
android.meta_data = 

# (list) Android library project to add (will be added in the
# project.properties automatically.)
android.library_references =

# (bool) Copy library instead of making a libpymodules.so
android.copy_libs = 1

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a, armeabi-v7a

# (int) Android API to use
android.api = 33

# (int) Minimum API required
android.minapi = 21

# (str) Android SDK version to use
android.sdk = 33

# (str) Android NDK version to use
android.ndk = 23b

# (str) Android build tools version to use
android.build_tools = 33.0.2

# (bool) Automatically accept SDK license
android.accept_sdk_license = True

# (str) Android SDK path (leave empty for auto-detection)
android.sdk_path = 

# (str) Android NDK path (leave empty for auto-detection)
android.ndk_path =

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
