#!/bin/sh

#   do_a_build.sh

set -e
git status
./scripts/01-build_installer_source.sh
./scripts/02-build_installer_binaries.sh
./scripts/03-build_signed_package.sh
# ---> codesign wants to use the python_certs keychain
# ---> also used by productsign
./scripts/03-cache_third_party_libraries.sh
./scripts/04-build_notorized_package.sh
# ---> notarytool uses a keychain profile
#      created with xcrun notarytool store-credentials
./scripts/05-upload_installer.sh
# ---> needs ssh key for psf dl server

exit 0
