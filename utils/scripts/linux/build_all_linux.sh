#!/usr/bin/env bash
set -e

recipes_repo=https://github.com/audacity/conan-recipes.git
recipes_branch=conan2

audacity3_repo=https://github.com/audacity/audacity.git
audacity3_branch=master
audacity3_build_order=build_order.yml
audacity3_build_config=audacity3

audacity4_repo=https://github.com/crsib/audacity.git
audacity4_branch=qt_conan2
audacity4_build_order=build_order_qt.yml
audacity4_build_config=audacity4

build () {
    local os_version=$1
    local gcc_version=$2
    local upload_build_tools=$3

    docker build \
        --build-arg="arg_ubuntu_version=${os_version}" \
        --build-arg="arg_gcc_version=${gcc_version}" \
        --build-arg="arg_upload_build_tools=${upload_build_tools}" \
        --build-arg="arg_recipes_repo=${recipes_repo}" \
        --build-arg="arg_recipes_branch=${recipes_branch}" \
        -t audacity-build-tools:${os_version}-${gcc_version} -f docker/Dockerfile docker

    docker run \
            --env "audacity_repo=${audacity3_repo}" \
            --env "audacity_branch=${audacity3_branch}" \
            --env "build_order=${audacity3_build_order}" \
            --env "build_config=${audacity3_build_config}" \
            --rm -it audacity-build-tools:${os_version}-${gcc_version}

    docker run \
            --env "audacity_repo=${audacity4_repo}" \
            --env "audacity_branch=${audacity4_branch}" \
            --env "build_order=${audacity4_build_order}" \
            --env "build_config=${audacity4_build_config}" \
            --rm -it audacity-build-tools:${os_version}-${gcc_version}
}

rm -fv *.log

build 20.04 9  true  2>&1 | tee build_20.04-9.log
build 20.04 10 false 2>&1 | tee build_20.04-10.log
build 20.04 11 false 2>&1 | tee build_20.04-11.log
build 22.04 12 false 2>&1 | tee build_22.04-12.log
build 22.04 13 false 2>&1 | tee build_22.04-13.log
