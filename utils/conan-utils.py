import argparse
import os
import sys
import traceback

import yaml
from dotenv import load_dotenv
from impl import conan, conan_env
from impl.config import directories
from impl.package_reference import PackageReference
from impl.profiles import ConanProfiles
from impl.update_mirror import update_mirror
from impl.upload import upload_all
from impl.debug import enable_debug_processors, finalize_debug_processors, discard_debug_data
from impl.remotes import add_remote, remove_remote, list_remotes
from impl.remote_cache import upload_cache, delete_cache, list_cache, process_conan_cache, process_debug_cache
from impl.build_order import get_build_order

load_dotenv()

def add_build_order_option(parser):
    parser.add_argument('--build-order', type=str, help='Path to file with build order. Relative paths are resolved against config directory', required=False)

def add_common_build_options(parser, allow_single_package=True):
    parser.add_argument('--profile-build', type=str, help='Conan build profile', required=False)
    parser.add_argument('--profile-host', type=str, help='Conan host profile', required=True)
    parser.add_argument('--keep-sources', action='store_true', help='Do not clean up sources after building')
    parser.add_argument('--enable-debug-processor', action='append', help='Enable specific debug processor (symstore, sentry)', required=False)
    parser.add_argument('--skip-debug-data-upload', action='store_true', help='Do not upload or discard debug data. Useful with store-cache command')
    add_build_order_option(parser)

    if allow_single_package:
        parser.add_argument('--package', type=str, help='Package name', required=False)
        parser.add_argument('--version', type=str, help='Package version', required=False)

def add_conan_command(subparser, name, description):
    subparser = subparser.add_parser(name, help=description)
    subparser.add_argument('--all', action='store_true', help='Execute command for all recipes in the directory. If not specified, only packages with config are processed', required=False)

def add_cache_options(parser, cache_id_required:bool, cache_id_present:bool):
    parser.add_argument('--group-id', type=str, help='Group ID', required=True)
    if cache_id_present:
        parser.add_argument('--cache-id', type=str, help='Cache ID', required=cache_id_required)
        parser.add_argument('--compression', type=str, help='Compression used (gz, bz2, xz, none)', required=False, default='xz')
    parser.add_argument('--remote', type=str, help='Artifactory remote (including repo)', required=False)
    parser.add_argument('--user', type=str, help='Artifactory user name', required=False)
    parser.add_argument('--password', type=str, help='Artifactory password', required=False)
    parser.add_argument('--key', type=str, help='Artifactory password', required=False)

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
    subparser.add_argument('--binaries-remote', type=str, help='Binaries remote', required=False)
    subparser.add_argument('--upload-build-tools', action='store_true', help='Upload build tools')
    add_build_order_option(subparser)

    #===========================================================================
    # update-mirror
    #===========================================================================
    subparser = subparsers.add_parser('update-mirror', help='Update sources on the Audacity mirror')
    subparser.add_argument('--remote', type=str, help='Mirror remote', required=False)
    subparser.add_argument('--user', type=str, help='Artifactory user name', required=False)
    subparser.add_argument('--password', type=str, help='Artifactory password', required=False)
    subparser.add_argument('--key', type=str, help='Artifactory password', required=False)
    subparser.add_argument('--all', action='store_true', help='Process all packages and versions', required=False)

    #===========================================================================
    # add-remote
    #===========================================================================
    subparser = subparsers.add_parser('add-remote', help='Add Conan remote')
    subparser.add_argument('--name', type=str, help='Remote name', required=True)
    subparser.add_argument('--url', type=str, help='Remote URL', required=True)

    #===========================================================================
    # list-remotes
    #===========================================================================
    subparsers.add_parser('list-remotes', help='List Conan remotes')

    #===========================================================================
    # remove-remote
    #===========================================================================
    subparser = subparsers.add_parser('remove-remote', help='Remove Conan remote')
    subparser.add_argument('--name', type=str, help='Remote name', required=True)

    #===========================================================================
    # validate-recipes
    #===========================================================================
    subparser = subparsers.add_parser('validate-recipe', help='Fill the cache with the build order and validates that recipe can consume all dependencies without building')
    add_common_build_options(subparser, allow_single_package=False)
    subparser.add_argument('--remote', action='append', help='Conan remote', required=False)
    subparser.add_argument('--recipe', type=str, help='Path to the recipe', required=True)
    subparser.add_argument('--recipe-config', type=str, help='Path to the config file for the recipe', required=True)
    subparser.add_argument('--export-recipes', action='store_true', help='Export recipes to Conan cache before building')

    #===========================================================================
    # store-cache
    #===========================================================================
    subparser = subparsers.add_parser('store-cache', help='Store Conan cache to Artifactory')
    add_cache_options(subparser, True, True)
    subparser.add_argument('--metadata-file', type=str, help='Path to the metadata file', required=False)

    #===========================================================================
    # delete-cache
    #===========================================================================
    subparser = subparsers.add_parser('delete-cache', help='Delete remote Conan cache')
    add_cache_options(subparser, False, True)

    #===========================================================================
    # list-cache
    #===========================================================================
    subparser = subparsers.add_parser('list-cache', help='List remote Conan cache')
    add_cache_options(subparser, False, False)

    #===========================================================================
    # process-conan-cache
    #===========================================================================
    subparser = subparsers.add_parser('process-conan-cache', help='Process remote Conan cache')
    add_cache_options(subparser, False, False)
    subparser.add_argument('--recipes-remote', type=str, help='Recipes remote', required=False)
    subparser.add_argument('--binaries-remote', type=str, help='Binaries remote', required=False)

    #===========================================================================
    # process-debug-cache
    #===========================================================================
    subparser = subparsers.add_parser('process-debug-cache', help='Process remote Conan cache')
    add_cache_options(subparser, False, False)


    return parser.parse_args()

def get_profiles(args):
    return ConanProfiles(args.profile_host, args.profile_build)

def resolve_recipe_config(args):
    if not args.recipe_config:
        return None

    if os.path.isabs(args.recipe_config):
        return args.recipe_config

    lookup_locations = args.recipe, directories.config_platform_packages_dir, directories.config_packages_dir, args.config_dir

    for directory in lookup_locations:
        if not directory or not os.path.isdir(directory):
            continue
        recipe_config = os.path.join(directory, args.recipe_config)
        if os.path.exists(recipe_config):
            return recipe_config
        recipe_config += '.yml'
        if os.path.exists(recipe_config):
            return recipe_config

    raise Exception('Recipe config file not found: {}'.format(args.recipe_config))

def get_package_reference(args):
    return PackageReference(args.package, args.version)

def run_conan_command(args):
    if args.subparser_name == 'build':
        if args.package:
            conan.build_package(get_package_reference(args), get_profiles(args), args.export_recipes, args.keep_sources)
        else:
            conan.build_all(get_build_order(args.build_order), get_profiles(args), args.export_recipes, args.keep_sources)
    elif args.subparser_name == 'install':
        if args.install_dir:
            directories.install_dir = args.install_dir

        if args.recipe:
            conan.install_recipe(args.recipe, resolve_recipe_config(args), get_profiles(args), args.remote, args.allow_build, args.keep_sources)
        elif args.package:
            conan.install_package(get_package_reference(args), get_profiles(args), args.remote, args.allow_build, args.keep_sources)
        else:
            conan.install_all(get_build_order(args.build_order), get_profiles(args), args.remote, args.allow_build, args.keep_sources)

    elif args.subparser_name == 'clean':
        conan.clean()
    elif args.subparser_name == 'upload':
        upload_all(args.recipes_remote, args.binaries_remote, args.upload_build_tools, get_build_order(args.build_order))
    elif args.subparser_name == 'add-remote':
        add_remote(args.name, args.url)
    elif args.subparser_name == 'list-remotes':
        print(list_remotes())
    elif args.subparser_name == 'remove-remote':
        remove_remote(args.name)
    elif args.subparser_name == 'validate-recipe':
        if args.export_recipes:
            conan.execute_conan_command('export-recipes', False)
        conan.install_all(get_build_order(args.build_order), get_profiles(args), args.remote, True, False)
        conan.install_recipe(args.recipe, resolve_recipe_config(args), get_profiles(args), args.remote, False, False)
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
    elif args.subparser_name == 'update-mirror':
        update_mirror(args.remote, args.user, args.password, args.key, args.all)
    elif args.subparser_name == 'store-cache':
        upload_cache(
            remote=args.remote,
            username=args.user,
            password=args.password,
            key=args.key,
            group_id=args.group_id,
            cache_id=args.cache_id,
            compression=args.compression,
            metadata_file=args.metadata_file)
    elif args.subparser_name == 'delete-cache':
        delete_cache(
            remote=args.remote,
            username=args.user,
            password=args.password,
            key=args.key,
            group_id=args.group_id,
            cache_id=args.cache_id,
            compression=args.compression)
    elif args.subparser_name == 'list-cache':
        print(list_cache(
            remote=args.remote,
            username=args.user,
            password=args.password,
            key=args.key,
            group_id=args.group_id))
    elif args.subparser_name == 'process-conan-cache':
        process_conan_cache(
            remote=args.remote,
            username=args.user,
            password=args.password,
            key=args.key,
            group_id=args.group_id,
            recipes_remote=args.recipes_remote,
            binaries_remote=args.binaries_remote)
    elif args.subparser_name == 'process-debug-cache':
        process_debug_cache(
            remote=args.remote,
            username=args.user,
            password=args.password,
            key=args.key,
            group_id=args.group_id)
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

    if hasattr(args, 'enable_debug_processor'):
        skip_upload = hasattr(args, 'skip_debug_data_upload') and args.skip_debug_data_upload
        enable_debug_processors(args.enable_debug_processor, skip_upload)

    try:
        main(args)
    except Exception as e:
        discard_debug_data()
        traceback.print_exc()
        sys.exit(1)
    finally:
        finalize_debug_processors()
