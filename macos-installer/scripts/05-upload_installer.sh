#!/bin/sh

#   upload_installer.sh

set -e

source ./scripts/00-build_settings.txt
source ./scripts/00-private_build_settings.txt

cd ./installer
cd ./variant

cd ./notarized-package

INSTALL_PKG="$( cat installer_pkg_name.txt )"

ssh ${BP_DOWNLOAD_SERVER} <<EOF1
    set --  "./${INSTALL_PKG}" \
        "./${INSTALL_PKG}.asc" \
        "${BP_DOWNLOAD_SERVER_DEVTEST}/${INSTALL_PKG}" \
        "${BP_DOWNLOAD_SERVER_DEVTEST}/${INSTALL_PKG}.asc"
    for f
    do
        [ -e \$f ] && echo "ERROR: "\$f" already exists on ${BP_DOWNLOAD_SERVER}" && exit 1
    done
    echo "here"
    exit 0
EOF1

set -- "${INSTALL_PKG}" "${INSTALL_PKG}.asc"
for f ; do
    if [ -e "${f}" ] ; then     
        scp -pr "./${f}" ${BP_DOWNLOAD_SERVER}:
        ssh ${BP_DOWNLOAD_SERVER} <<EOF2
            chmod 664 "./${f}" && \
            chgrp downloads "./${f}" && \
            cp -pr "./${f}" "${BP_DOWNLOAD_SERVER_DEVTEST}/"
EOF2
        curl -X PURGE "${BP_DOWNLOAD_SERVER_DEVTEST_URL}/${f}"
    fi
done

exit 0
