import argparse
import os
import sys

import yaml
from dotenv import load_dotenv
from impl import conan, conan_env
from impl.config import directories
from impl.package_reference import PackageReference
from impl.profiles import ConanProfiles
from impl.upload import upload_all

load_dotenv()

def add_common_build_options(parser):
    parser.add_argument('--profile-build', type=str, help='Conan build profile', required=False)
    parser.add_argument('--profile-host', type=str, help='Conan host profile', required=True)
    parser.add_argument('--package', type=str, help='Package name', required=False)
    parser.add_argument('--version', type=str, help='Package version', required=False)
    parser.add_argument('--keep-sources', action='store_true', help='Do not clean up sources after building')
    parser.add_argument('--build-order', type=str, help='Path to file with build order. Relative paths are resolved against config directory', required=False)

def add_conan_command(subparser, name, description):
    subparser = subparser.add_parser(name, help=description)
    subparser.add_argument('--all', action='store_true', help='Execute command for all recipes in the directory. If not specified, only packages with config are processed', required=False)

def parse_args():
    parser = argparse.ArgumentParser(description='Audacity Conan Utils')

    # Common options for all commands
    parser.add_argument('--recipes-dir', type=str, help='Path to recipes directory', required=False)
    parser.add_argument('--config-dir', type=str, help='Path to config directory', required=False)
    parser.add_argument('--venv-dir', type=str, help='Path to virtual environment where Conan is installed', required=False)
    parser.add_argument('--conan-home-dir', type=str, help='Path to Conan home directory', required=False)
    parser.add_argument('--output-dir', type=str, help='Path to output directory. Overrides venv-dir and conan-home-dir.', required=False)

    subparsers = parser.add_subparsers(help='sub-command help', dest='subparser_name')

    #===========================================================================
    # init-env
    #===========================================================================
    subparser = subparsers.add_parser('init-env', help='Initialize Conan environment')
    subparser.add_argument('--clean', action='store_true', help='Create a clean Conan environment')

    #===========================================================================
    # print-env
    #===========================================================================
    subparser = subparsers.add_parser('print-env', help='Print Conan environment')
    subparser.add_argument('--path', action='store_true', help='Print path to Conan')
    subparser.add_argument('--home', action='store_true', help='Print path to Conan home directory')
    subparser.add_argument('--version', action='store_true', help='Print Conan version')

    #===========================================================================
    # clean
    #===========================================================================
    subparsers.add_parser('clean', help='Cleanup Conan cache')

    #===========================================================================
    # export-recipes
    #===========================================================================
    add_conan_command(subparsers, 'export-recipes', 'Export bundled recipes to Conan cache')

    #===========================================================================
    # update-sources
    #===========================================================================
    add_conan_command(subparsers, 'update-sources', 'Download package sources to Conan cache')

    #===========================================================================
    # build
    #===========================================================================
    subparser = subparsers.add_parser('build', help='Build packages')
    add_common_build_options(subparser)
    subparser.add_argument('--export-recipes', action='store_true', help='Export recipes to Conan cache before building')

    #===========================================================================
    # install
    #===========================================================================
    subparser = subparsers.add_parser('install', help='''
    Install packages, either from remote or from local recipes.
    If --recipe is specified, --package and --version are ignored and all dependencies must be satisfied from the Conan cache.''')

    add_common_build_options(subparser)
    subparser.add_argument('--remote', action='append', help='Conan remote', required=False)
    subparser.add_argument('--recipe', type=str, help='Path to the recipe', required=False)
    subparser.add_argument('--recipe-config', type=str, help='Path to the config file for the recipe', required=False)
    subparser.add_argument('--allow-build', action='store_true', help='Allow building from source')
    subparser.add_argument('--install-dir', type=str, help='Path to install directory', required=False)

    #===========================================================================
    # upload
    #===========================================================================
    subparser = subparsers.add_parser('upload', help='Upload packages to remote')
    subparser.add_argument('--recipes-remote', type=str, help='Recipes remote', required=False)
    subparser.add_argument('--recipes-binaries', type=str, help='Binaries remote', required=False)

    return parser.parse_args()

def get_profiles(args):
    return ConanProfiles(args.profile_host, args.profile_build)

def get_build_order_path(args):
    if args.build_order:
        if os.path.isabs(args.build_order):
            return args.build_order
        return os.path.join(directories.config_dir, args.build_order)
    else:
        return os.path.join(directories.config_dir, 'build_order.yml')

def resolve_recipe_config(args):
    if not args.recipe_config:
        return None

    if os.path.isabs(args.recipe_config):
        return args.recipe_config

    lookup_locations = args.recipe, directories.config_platform_packages_dir, directories.config_packages_dir, args.config_dir

    for directory in lookup_locations:
        recipe_config = os.path.join(directory, args.recipe_config)
        if os.path.exists(recipe_config):
            return recipe_config
        recipe_config += '.yml'
        if os.path.exists(recipe_config):
            return recipe_config

    raise Exception('Recipe config file not found: {}'.format(args.recipe_config))

def get_build_order(args):
    build_order_path = get_build_order_path(args)
    if not os.path.exists(build_order_path):
        raise Exception('Build order file does not exist: {}'.format(build_order_path))

    with open(build_order_path, 'r') as f:
        config = yaml.safe_load(f)['build_order']
        build_order = []

        for part in config:
            build_on = part['platforms']
            if build_on == '*' or sys.platform.lower() in build_on:
                build_order += part['packages']

    return build_order


def get_package_reference(args):
    return PackageReference(args.package, args.version)

def run_conan_command(args):
    if args.subparser_name == 'build':
        if args.package:
            conan.build_package(get_package_reference(args), get_profiles(args), args.export_recipes, args.keep_sources)
        else:
            conan.build_all(get_build_order(args), get_profiles(args), args.export_recipes, args.keep_sources)
    elif args.subparser_name == 'install':
        if args.install_dir:
            directories.install_dir = args.install_dir

        if args.recipe:
            conan.install_recipe(args.recipe, resolve_recipe_config(args), get_profiles(args), args.remote, args.allow_build, args.keep_sources)
        elif args.package:
            conan.install_package(get_package_reference(args), get_profiles(args), args.remote, args.allow_build, args.keep_sources)
        else:
            conan.install_all(get_build_order(args), get_profiles(args), args.remote, args.allow_build, args.keep_sources)

    elif args.subparser_name == 'clean':
        conan.clean()
    elif args.subparser_name == 'upload':
        upload_all(args.recipes_remote, args.recipes_binaries)
    else:
        conan.execute_conan_command(args.subparser_name, args.all)

def main(args):
    if args.subparser_name == 'init-env':
        conan_env.create_conan_environment(clean=args.clean)
    elif args.subparser_name == 'print-env':
        if args.path:
            print(conan_env.get_conan_path())
        if args.home:
            print(conan_env.get_conan_home_path())
        if args.version:
            print(conan_env.get_conan_version())
    else:
        with conan_env.ConanEnv():
            run_conan_command(args)

if __name__ == "__main__":
    args = parse_args()

    if args.recipes_dir:
        directories.recipes_dir = args.recipes_dir
    if args.config_dir:
        directories.config_dir = args.config_dir
    if args.venv_dir:
        directories.venv_dir = args.venv_dir
    if args.conan_home_dir:
        directories.conan_home_dir = args.conan_home_dir
    if args.output_dir:
        directories.change_output_dir(args.output_dir)


    main(args)
