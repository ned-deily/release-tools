PSF macOS Installer Builds 
==========================

2025-02-11

**NOTE** This is a snapshot of the evolving build process for Python
Software Foundation cpython macOS installer builds as published on the
python.org website. The process is currently in transition from a specific
private multiple Intel Mac virtual machine environment to a more general
environment that can be used by Python release managers on all Macs running
current versions of macOS and eventually automatically in cloud environments.
The build process has evolved slowly over many years. This snapshot is a step
in the journey.

Current known limitations of this snapshot:

- building tested on current macOS 14 Sonoma systems (14.5) or later using
  Xcode 16.2. Should also be able to be used with current Apple Command Line
  Tools, not recently tested.

- built installer can be deployed on macOS 10.15 and newer systems

- the build process may not provide complete isolation from the user's build
  environment. Use of a separate user account for building should be considered.

- currently only one build may be in progress at a time on a particular system
  (should no longer be true but not yet tested)

- the builder should have an Apple Developer Connection account

- the builder will need access to Developer ID Application and Developer ID
  Installer certificates issued by Apple to the PSF Apple Developer account
  in order to codesign build binary artifacts and installer packages.

- to meet Apple Gatekeeper security requirements, the built installer package
  must complete Apple's notarization process for macOS downloads.

One-time setup:

- Obtain copy of macOS keychain with PSF Developer ID Installer certificates

- Create app-specific password for your Apple ID and save it in a notarytool
  keychain profile as described here:
  https://developer.apple.com/documentation/security/customizing-the-notarization-workflow?language=objc#Upload-your-app-to-the-notarization-service

  You will include the keychain file name and the notarytool keychain profile
  name in your 00-private_build_settings.txt below.

Build steps outline:

- Clone / checkout this repo under a macOS user. 

- Currently the build process is implemented as a set of scripts in the
  scripts directory. They must be run manually in sequence from a terminal
  shell.

The steps:

git clone or unpack source bundle

cd build_macos_installer

cd scripts

cp 00-build_settings-pre.txt 00-build_settings.txt
$EDITOR 00-build_settings.txt # customize build settings here

cp 00-private_build_settings-pre.txt 00-private_build_settings.txt
$EDITOR 00-private_build_settings.txt # customize security-related settings here

cd ..

rm -rf ./source ./cached-artifacts # manually clean cpython source snapshot

Note, that steps 01 through 05 can be performed by the do_a_build.sh umbrella
script in the top level. However, in case of unexpected problems, it may
be useful to re-run those steps individually. 

./scripts/01-build_installer_source.sh

rm -rf ./installer # manually clean build tree

./scripts/02-build_installer_binaries.sh

./scripts/03-build_signed_package.sh

# optionally, save the just-built third-party libraries (OpenSSL, Tcl/Tk, etc)
#   if you expect to rerun the 02-build_installer_binaries.sh 
#   or 03-build_sign_package.sh steps

./scripts/03-cache_third_party_libraries

# Submit installer package to Apple Notarization Service and wait for completion (typically no more than 5 minutes)

./scripts/04-build_notorized_package.sh

# uploads notarized installer to a test location on the PSF download server and to your home directory there.

./scripts/05-upload_installer.sh


# Optionally, test installer on ssh-connected test VM or system image.
# Currently, only downloads test scripts to the remote Desktop folder.
# Manual intervention is needed to install, run, and save results locally.
# WARNING, the testing step is currently potentially DESTRUCTIVE
# on the remote test machine, i.e. it may delete previously installed Pythons, etc.

./scripts/06-test_installer.sh <remote-ssh-id> # DESTRUCTIVE!

# retrieve test results that have been manually saved from the remote Terminal session

./scripts/06-retrieve_test_results.sh <remote-ssh-id>

# Currently, displays reminder to move pkg file into release download directory

./scripts/07-handoff_to_release_manager.sh

# Remove installer package from test location on download server and purges its CDN cache

./scripts/08-cleanup_testing.sh

----------
