import subprocess
import os

from impl import utils
from impl import conan_recipe_store
from impl.package_reference import PackageReference
from impl.files import safe_rm_tree


def get_cache_path(folder, package_reference:PackageReference):
    cmd = [utils.get_conan(), 'cache', 'path', str(package_reference)]

    if folder != "export":
        cmd += ['--folder', folder]

    return subprocess.check_output(cmd).decode('utf-8').strip()


def get_cache_path_export(package_reference:PackageReference):
    return get_cache_path('export', package_reference)


def get_cache_path_export_source(package_reference:PackageReference):
    return get_cache_path('export_source', package_reference)


def get_cache_path_source(package_reference:PackageReference):
    cache_path = get_cache_path('source', package_reference)

    if os.path.isdir(cache_path):
        return cache_path

    return conan_recipe_store.get_recipe(package_reference).local_source_dir


def clean_cache(package_reference:PackageReference, sources:bool=False, builds:bool=True, downloads:bool=True, temp:bool=True, all:bool=False):
    print(f"Cleaning cache for `{package_reference}`...")

    cmd = [
        utils.get_conan(), 'cache', 'clean',
        str(package_reference),
    ]

    if not all:
        if sources:
            cmd += ['--source']

        if builds:
            cmd += ['--build']

        if downloads:
            cmd += ['--download']

        if temp:
            cmd += ['--temp']

    subprocess.check_call(cmd)

    # Running cache clean is not sufficient, as we are in "local" mode
    # Sources are in downloaded to the recipe folder, builds paths are local as well,
    # we neet to clean them manually
    if all or sources:
        cache_path = get_cache_path_source(package_reference)
        safe_rm_tree(cache_path)

    recipe = conan_recipe_store.get_recipe(package_reference)

    if all or builds:
        for path in recipe.local_build_dirs:
            safe_rm_tree(path)

    # Conan provides no way to cleanup test folders
    for path in recipe.local_test_build_dirs:
        safe_rm_tree(path)
