import os
import subprocess
from impl import conan_recipe_store
from impl import package_config
from impl import conan_env
from impl import utils
from impl import cache

def get_recipe_stores(path:str, with_config_only:bool):
    for recipe in os.listdir(path):
        recipe_path = os.path.join(path, recipe)
        if not os.path.isdir(recipe_path):
            continue

        if not with_config_only:
            yield conan_recipe_store.ConanRecipeStore(recipe_path)

        if package_config.PackageConfig().get_package_config(recipe):
            yield conan_recipe_store.ConanRecipeStore(recipe_path)


def execute_conan_command(path:str, command:str, all:bool):
    for recipe_store in get_recipe_stores(path, not all):
        recipe_store.execute_command(command, all)

def build_package(path:str, package:str, version:str=None, host_profile:str=None, build_profile:str=None, export_recipe:bool=False):
    config = package_config.PackageConfig()

    user = config.get_package_user(package, version)
    channel = config.get_package_channel(package, version)

    if not version:
        pkg_config = config.get_package_config(package)

        if not pkg_config:
            raise Exception(f'No config found for package {package}')

        version = pkg_config['version']

    recipe_store = conan_recipe_store.ConanRecipeStore(os.path.join(path, package))

    clean_sources = False

    try:
        if export_recipe:
            recipe_store.export(version)

        sources_location = cache.get_cache_path_source(package, version, user, channel)
        clean_sources = not os.path.isdir(sources_location)

        if clean_sources:
            recipe_store.source(version)

        recipe_store.build(package, version, host_profile, build_profile)
    finally:
        cache.clean_cache(
            package, version,
            user, channel,
            sources=clean_sources)


def build_packages(path:str, package:str=None, version:str=None, host_profile:str=None, build_profile:str=None, export_recipes:bool=False):
    if package:
        return build_package(path, package, version, host_profile, build_profile, export_recipes)

    for package in package_config.PackageConfig().get_build_order():
        build_package(path, package, version, host_profile, build_profile, export_recipes)


def clean():
    with conan_env.ConanEnv():
        subprocess.check_call([utils.get_conan(), 'cache', 'clean', '*'])
        subprocess.check_call([utils.get_conan(), 'remove', '--confirm', '*'])
