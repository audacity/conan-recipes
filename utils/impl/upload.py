import os
from impl.remotes import add_remote, remove_remote
from impl.conan_recipe_store import get_recipe
from impl.package_reference import PackageReference

recipes_remote_name = "conan-utils-audacity-recipes-conan2"
binaries_remote_name = "conan-utils-audacity-binaries-conan2"


def upload_all(recipes_remote:str, binaries_remote:str, upload_build_tools:bool, build_order:list[str]) -> None:
    if not recipes_remote:
        recipes_remote = os.environ.get('CONAN_RECIPES_REMOTE', "https://artifactory.audacityteam.org/artifactory/api/conan/audacity-recipes-conan2")
    if not binaries_remote:
        binaries_remote = os.environ.get('CONAN_BINARIES_REMOTE', "https://artifactory.audacityteam.org/artifactory/api/conan/audacity-binaries-conan2")

    recipes_added = add_remote(recipes_remote_name, recipes_remote)
    binaries_added = add_remote(binaries_remote_name, binaries_remote)

    failed_packages = []

    try:
        for package_name in build_order:
            package_reference = PackageReference(package_name=package_name)
            recipe = get_recipe(package_reference)

            if not recipe.is_build_tool or upload_build_tools:
                print(f'Uploading {package_reference}', flush=True)
                try:
                    recipe.upload(recipes_remote_name, False)
                    recipe.upload(binaries_remote_name, True)
                except Exception as e:
                    print(f'Failed to upload {package_reference}: {e}', flush=True)
                    failed_packages.append(package_reference)
            else:
                print(f'Skipping {package_reference}: a build tool', flush=True)
    finally:
        if recipes_added:
            remove_remote(recipes_remote_name)
        if binaries_added:
            remove_remote(binaries_remote_name)

        if len(failed_packages) > 0:
            print('Failed to upload the following packages:', flush=True)
            for package_reference in failed_packages:
                print(f'  {package_reference}', flush=True)
            raise Exception('Failed to upload some packages')

