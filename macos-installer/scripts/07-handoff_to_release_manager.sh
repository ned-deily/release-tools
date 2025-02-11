#!/bin/sh

#   handoff_to_release_manager.sh

set -e

source ./scripts/00-build_settings.txt
source ./scripts/00-private_build_settings.txt

cd ./installer
cd ./variant

cd ./notarized-package

INSTALL_PKG="$( cat installer_pkg_name.txt )"

echo " -- ssh to download server and mv -i ${INSTALL_PKG} to release directory in ${BP_DOWNLOAD_SERVER_PYTHON}"
echo " "
echo " -- reply to release manager email with package information:"
echo " "
cat ./email.txt
echo " "

exit 0
