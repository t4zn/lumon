# Lumon Android APK

## Overview
This directory contains the Android APK build for Lumon - AI Plant Expert, a native Android application built from the Lumon web project files.

## APK Features
- **Native Android App**: Built with Capacitor for optimal performance
- **Camera Integration**: Direct access to device camera for plant photography
- **Offline Capable**: Core UI functions work without internet connection
- **Plant Identification**: AI-powered plant recognition using device photos
- **Material Design**: Native Android look and feel
- **Full Screen**: Immersive mobile experience
- **Inter Typography**: Consistent font styling throughout the app

## Build Process
The APK is generated using Capacitor, which wraps the Lumon web application in a native Android container:

1. **Web Assets**: All static files, templates, and scripts are bundled
2. **Native Bridge**: Capacitor provides native device API access
3. **Camera Permissions**: Android manifest includes camera and storage permissions
4. **Production Build**: Optimized APK ready for distribution

## Installation
To install the APK on an Android device:

1. Download the APK file from the build output
2. Enable "Install from unknown sources" in Android settings
3. Open the APK file to install
4. Grant camera permissions when prompted

## Technical Details
- **Platform**: Android (API 21+)
- **Framework**: Capacitor + WebView
- **Bundle Size**: Optimized for mobile distribution
- **Permissions**: Camera, Storage, Internet
- **Theme**: Adaptive light/dark mode support

## File Structure
```
android/
├── app/
│   ├── build/
│   │   └── outputs/
│   │       └── apk/
│   │           └── debug/
│   │               └── app-debug.apk
│   └── src/
│       └── main/
│           ├── assets/
│           │   └── www/
│           │       ├── static/
│           │       └── templates/
│           └── AndroidManifest.xml
└── gradle/
```

## Distribution
The APK can be:
- Installed directly on Android devices
- Distributed via file sharing
- Uploaded to Google Play Store (with proper signing)
- Shared through APK distribution platforms

## Notes
- Built from Lumon web project source files
- Maintains full functionality of the web version
- Optimized for mobile performance
- Ready for production deployment
