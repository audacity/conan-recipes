import json
import os
import subprocess
import yaml

from impl import cache, utils
from impl.conan_recipe_store import get_recipe, get_recipe_stores
from impl.config import directories
from impl.package_reference import PackageReference
from impl.profiles import ConanProfiles
from impl.debug import handle_build_completed


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


def install_recipe(recipe_path:str, config_path:str, profiles:ConanProfiles, remotes:list[str], allow_build:bool, keep_sources:bool):
    try:
        cmd = [
            utils.get_conan(), 'install',
            '-of', directories.install_dir,
            '-vvv',
            '-pr:h', profiles.host_profile,
            '-pr:b', profiles.build_profile,
            '--format', 'json'
        ]

        if allow_build:
            cmd += ['--build', 'missing']

        if remotes and len(remotes) > 0:
            for remote in remotes:
                cmd += ['-r', remote]
        else:
            cmd += ['--no-remote']

        if config_path:
            print(f'Loading options from {config_path}')
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)['config']
                print(config)
                if 'options' in config:
                    for opt in config['options'].split():
                        cmd += ['-o:h', opt.strip()]

        cmd += [recipe_path]
        print(cmd)

        dependecies_graph = json.loads(subprocess.check_output(cmd))['graph']['nodes']

        for node in dependecies_graph.values():
            if node['id'] == '0':
                continue

            ref = node['ref']
            package_id = node['package_id']

            print(f'Collecting directories for {ref}:{package_id}')

            source_dir = subprocess.check_output([utils.get_conan(), 'cache', 'path', '--folder', 'source', ref]).decode('utf-8').strip()
            build_dir = subprocess.check_output([utils.get_conan(), 'cache', 'path', '--folder', 'build', f'{ref}:{package_id}']).decode('utf-8').strip()

            handle_build_completed(PackageReference(package_reference=ref), source_dir, build_dir)
    finally:
        print('Cleaning cache...')
        if not keep_sources:
            subprocess.check_call([utils.get_conan(), 'cache', 'clean', '*'])
        else:
            subprocess.check_call([utils.get_conan(), 'cache', 'clean', '*', '--temp', '--build', '--download'])

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
