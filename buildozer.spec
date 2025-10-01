[app]

# (str) Title of your application
title = Emaktab Auto

# (str) Package name
package.name = emaktabauto

# (str) Package domain (reverse DNS style)
package.domain = org.emaktab

# (str) Source code where the main.py live
source.dir = .

# (str) Application versioning
version = 0.1

# (list) Application requirements
# ВАЖНО: сюда добавь все зависимости, которые используешь
requirements = python3,kivy,requests,beautifulsoup4

# (str) Presplash of the application
presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
icon.filename = %(source.dir)s/data/icon.png

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0


[buildozer]

# (int) Android API to use
android.api = 33

# (int) Minimum API your APK will support
android.minapi = 21

# (str) Android SDK version to use
android.sdk = 33

# (str) Android NDK version to use
android.ndk = 21e

# (str) Build tools version
android.build_tools = 33.0.2

# (str) Application format: apk, aab, universal
android.arch = armeabi-v7a, arm64-v8a, x86, x86_64

# (str) Accept SDK license automatically
android.accept_sdk_license = True

# (str) python-for-android branch
p4a.branch = develop

# (str) Command line to launch the app
# Если нужен конкретный entrypoint:
# entrypoint = main.py