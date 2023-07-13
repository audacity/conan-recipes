#!/usr/bin/env bash
set -e

ls -la /home
ls -la /home/user

python3 --version

git clone --depth 1 ${recipes_repo}  --branch ${recipes_branch}
git clone --depth 1 ${audacity_repo} --branch ${audacity_branch}

pip3 install -r conan-recipes/utils/requirements.txt

python3 conan-recipes/utils/conan-utils.py init-env --clean
python3 conan-recipes/utils/conan-utils.py add-remote --name conan-utils-audacity-binaries-conan2 --url https://artifactory.audacityteam.org/artifactory/api/conan/audacity-binaries-conan2

python3 conan-recipes/utils/conan-utils.py export-recipes --build-order ${build_order}

python3 conan-recipes/utils/conan-utils.py validate-recipe \
        --remote conan-utils-audacity-binaries-conan2 --profile-host host/linux/gcc${gcc_version}_x86_64_rel --profile-build build/linux/gcc${gcc_version}_x86_64 \
        --build-order ${build_order} --recipe-config ${build_config} --recipe audacity/conan/conanfile.py --enable-debug-processor sentry

python3 conan-recipes/utils/conan-utils.py validate-recipe \
        --remote conan-utils-audacity-binaries-conan2 --profile-host host/linux/gcc${gcc_version}_x86_64_deb --profile-build build/linux/gcc${gcc_version}_x86_64 \
        --build-order ${build_order} --recipe-config ${build_config} --recipe audacity/conan/conanfile.py

if [ "${upload_build_tools}" == "true"]; then
    python3 conan-recipes/utils/conan-utils.py upload --build-order ${build_order} --upload-build-tools
else
    python3 conan-recipes/utils/conan-utils.py upload --build-order ${build_order}
fi
