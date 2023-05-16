import subprocess
import os
import time

from impl import conan_env
from impl import utils
from impl import conan_recipe_store


def get_package_reference(package_name:str, package_version:str, user:str, channel:str):
    return f"{package_name}/{package_version}@{user}/{channel}"

def get_cache_path(folder, package_name:str, package_version:str, user:str, channel:str):
    with conan_env.ConanEnv():
        cmd = [utils.get_conan(), 'cache', 'path', get_package_reference(package_name, package_version, user, channel)]

        if folder != "export":
            cmd += ['--folder', folder]

        return subprocess.check_output(cmd).decode('utf-8').strip()


def get_cache_path_export(package_name:str, package_version:str, user:str, channel:str):
    return get_cache_path('export', package_name, package_version, user, channel)


def get_cache_path_export_source(package_name:str, package_version:str, user:str, channel:str):
    return get_cache_path('export_source', package_name, package_version, user, channel)


def get_cache_path_source(package_name:str, package_version:str, user:str, channel:str):
    cache_path = get_cache_path('source', package_name, package_version, user, channel)

    if os.path.isdir(cache_path):
        return cache_path

    return conan_recipe_store.get_recipe_store(package_name).get_source_folder(package_version)


def clean_cache(package_name:str, package_version:str, user:str, channel:str, sources:bool=False, builds:bool=True, downloads:bool=True, temp:bool=True, all:bool=False):
    print(f"Cleaning cache for `{package_name}/{package_version}@{user}/{channel}`...")
    with conan_env.ConanEnv():
        cmd = [
            utils.get_conan(), 'cache', 'clean',
            get_package_reference(package_name, package_version, user, channel),
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

    def safe_rm_tree(path):
        import shutil

        if not os.path.isdir(path):
            return

        def onerror(func, path, exc_info):
            import stat
            # Is the error an access error?
            if not os.access(path, os.W_OK):
                print(f"Failed to remove `{path}`. Trying to change permissions...")
                os.chmod(path, stat.S_IWUSR)
                func(path)
            else:
                raise OSError("Cannot change permissions for {}! Exception info: {}".format(path, exc_info))

        for i in range(20):
            try:
                shutil.rmtree(path, onerror=onerror)
                return
            except Exception as e:
                delay = 0.5 * float(i + 1)
                print(f"Failed to remove `{path}`: `{e}`. Retrying in {delay} seconds...")
                time.sleep(delay)

    # Running cache clean is not sufficient, as we are in "local" mode
    # Sources are in downloaded to the recipe folder, builds paths are local as well,
    # we neet to clean them manually
    if all or sources:
        cache_path = get_cache_path_source(package_name, package_version, user, channel)
        safe_rm_tree(cache_path)

    if all or builds:
        path = conan_recipe_store.get_recipe_store(package_name).get_build_folder(package_version)
        safe_rm_tree(path)

    # Conan provides no way to cleanup test folders
    folders = ('build', 'build-relwithdebinfo', 'build-minsizerel', 'build-release', 'build-debug')

    for folder in folders:
        tests_path = os.path.join(conan_recipe_store.get_recipe_store(package_name).get_recipe_folder(package_version), 'test_package', folder)
        safe_rm_tree(tests_path)

        tests_path = os.path.join(conan_recipe_store.get_recipe_store(package_name).get_recipe_folder(package_version), 'test_v1_package', folder)
        safe_rm_tree(tests_path)
