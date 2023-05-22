import os
import subprocess
from impl.conan_recipe_store import ConanRecipeStore, get_recipe
from impl.package_reference import PackageReference
from impl.package_config_provider import package_config_provider
from impl.config import directories
from impl.profiles import ConanProfiles
from impl import utils
from impl import cache

def get_recipe_stores(with_config_only:bool):
    path = directories.recipes_dir

    for recipe in os.listdir(path):
        recipe_path = os.path.join(path, recipe)
        if not os.path.isdir(recipe_path):
            continue

        if not with_config_only:
            yield ConanRecipeStore(recipe)

        if package_config_provider.get_package_config(recipe):
            yield ConanRecipeStore(recipe)


def execute_conan_command(command:str, all:bool):
    for recipe_store in get_recipe_stores(not all):
        recipe_store.execute_command(command, all)


def build_package(package_reference:PackageReference, profiles: ConanProfiles, export_recipe:bool=False, keep_sources:bool=False):
    recipe = get_recipe(package_reference)

    retrieve_sources = False

    try:
        if export_recipe:
            recipe.export()

        sources_location = cache.get_cache_path_source(package_reference)
        retrieve_sources = not os.path.isdir(sources_location)

        if retrieve_sources:
            recipe.source()

        recipe.build(profiles)
    finally:
        cache.clean_cache(package_reference, sources=retrieve_sources and not keep_sources)


def build_all(build_order:list[str], profiles:ConanProfiles, export_recipes:bool=False, keep_sources:bool=False):
    for package_name in build_order:
        build_package(PackageReference(package_name=package_name), profiles, export_recipes, keep_sources)


def clean():
    subprocess.check_call([utils.get_conan(), 'cache', 'clean', '*'])
    subprocess.check_call([utils.get_conan(), 'remove', '--confirm', '*'])


def install_recipe(path:str, profiles:ConanProfiles, remotes:list[str], allow_build:bool, keep_sources:bool):
    pass


def install_package(package_reference:PackageReference, profiles:ConanProfiles, remotes:list[str], allow_build:bool, keep_sources:bool):
    recipe = get_recipe(package_reference)

    try:
        recipe.install(profiles, remotes, allow_build)
    except subprocess.CalledProcessError as e:
        recipe.export()
        recipe.install(profiles, remotes, allow_build)
    finally:
        cache.clean_cache(package_reference, sources=not keep_sources)


def install_all(build_order:list[str], profiles:ConanProfiles, remotes:list[str], allow_build:bool, keep_sources:bool):
    for package_name in build_order:
        install_package(PackageReference(package_name=package_name), profiles, remotes, allow_build, keep_sources)
