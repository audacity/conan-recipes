#!/usr/bin/env bash
set -e

audacity3_repo=https://github.com/audacity/audacity.git
audacity3_branch=master
audacity3_build_order=build_order.yml
audacity3_build_config=audacity3

audacity4_repo=https://github.com/crsib/audacity.git
audacity4_branch=qt_conan2
audacity4_build_order=build_order_qt.yml
audacity4_build_config=audacity4

scriptLocation=$(dirname "$(readlink -f "$0")")

build_arch=$(uname -m)
xcode_version=$(xcodebuild -version | grep Xcode | cut -d' ' -f2 | cut -d'.' -f1)

build_profile="apple_clang${xcode_version}_${build_arch}"
build_dir="${scriptLocation}/${build_profile}"

conan_utils=$(readlink ${scriptLocation}/../../conan-utils.py)

mkdir -p ${build_dir}
pushd ${build_dir}

#python3 ${conan_utils} init-env --clean
python3 ${conan_utils} add-remote --name conan-utils-audacity-binaries-conan2 --url https://artifactory.audacityteam.org/artifactory/api/conan/audacity-binaries-conan2

trap popd && rm -Rf ${build_dir}

rm -Rf audacity
git clone --depth 1 ${audacity3_repo} --branch ${audacity3_branch}

python3 ${conan_utils} export-recipes --build-order ${audacity3_build_order}

python3 ${conan_utils} validate-recipe \
        --remote conan-utils-audacity-binaries-conan2 --profile-host host/macos/apple_clang${xcode_version}_${build_arch}_rel --profile-build build/macos/${build_profile} \
        --build-order ${audacity3_build_order} --recipe-config ${audacity3_build_config} --recipe audacity/conan/conanfile.py --enable-debug-processor sentry

python3 ${conan_utils} validate-recipe \
        --remote conan-utils-audacity-binaries-conan2 --profile-host host/macos/apple_clang${xcode_version}_${build_arch}_deb --profile-build build/macos/${build_profile} \
        --build-order ${audacity3_build_order} --recipe-config ${audacity3_build_config} --recipe audacity/conan/conanfile.py --enable-debug-processor sentry

rm -Rf audacity
git clone --depth 1 ${audacity4_repo} --branch ${audacity4_branch}

python3 ${conan_utils} export-recipes --build-order ${audacity4_build_order}

python3 ${conan_utils} validate-recipe \
        --remote conan-utils-audacity-binaries-conan2 --profile-host host/macos/apple_clang${xcode_version}_${build_arch}_rel --profile-build build/macos/${build_profile} \
        --build-order ${audacity4_build_order} --recipe-config ${audacity4_build_config} --recipe audacity/conan/conanfile.py --enable-debug-processor sentry

python3 ${conan_utils} validate-recipe \
        --remote conan-utils-audacity-binaries-conan2 --profile-host host/macos/apple_clang${xcode_version}_${build_arch}_deb --profile-build build/macos/${build_profile} \
        --build-order ${audacity4_build_order} --recipe-config ${audacity4_build_config} --recipe audacity/conan/conanfile.py --enable-debug-processor sentry

rm -Rf audacity

python3 ${conan_utils} upload --build-order ${audacity3_build_order} --upload-build-tools
python3 ${conan_utils} upload --build-order ${audacity4_build_order} --upload-build-tools
