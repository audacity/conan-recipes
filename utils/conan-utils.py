import argparse
import os
from impl import conan_env
from impl import conan
from impl import utils

def parse_args():
    parser = argparse.ArgumentParser(description='Audacity Conan Utils')
    subparsers = parser.add_subparsers(help='sub-command help', dest='subparser_name')

    parser_init_env = subparsers.add_parser('init-env', help='Initialize Conan environment')
    parser_init_env.add_argument('--clean', action='store_true', help='Clean Conan environment')

    parser_print_env = subparsers.add_parser('print-env', help='Print Conan environment')
    parser_print_env.add_argument('--path', action='store_true', help='Print path to Conan')
    parser_print_env.add_argument('--home', action='store_true', help='Print path to Conan home directory')
    parser_print_env.add_argument('--version', action='store_true', help='Print Conan version')

    parser_export_recipes = subparsers.add_parser('export-recipes', help='Export bundled recipes to Conan cache')
    parser_export_recipes.add_argument('--path', type=str, help='Path to recipes directory', required=False)
    parser_export_recipes.add_argument('--all', action='store_true', help='Export all recipes')

    parser_update_sources = subparsers.add_parser('update-sources', help='Download package sources to Conan cache')
    parser_update_sources.add_argument('--path', type=str, help='Path to recipes directory', required=False)
    parser_update_sources.add_argument('--all', action='store_true', help='Export all recipes')

    parser_build = subparsers.add_parser('build', help='Build packages')
    parser_build.add_argument('--path', type=str, help='Path to recipes directory', required=False)
    parser_build.add_argument('--package', type=str, help='Package name', required=False)
    parser_build.add_argument('--version', type=str, help='Package version', required=False)
    parser_build.add_argument('--profile-build', type=str, help='Conan build profile', required=False)
    parser_build.add_argument('--profile-host', type=str, help='Conan host profile', required=True)
    parser_build.add_argument('--export-recipes', action='store_true', help='Export recipes to Conan cache before building')

    subparsers.add_parser('clean', help='Cleanup Conan cache')

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.subparser_name == 'init-env':
        conan_env.create_conan_environment(clean=args.clean)
    elif args.subparser_name == 'print-env':
        if args.path:
            print(conan_env.get_conan_path())
        if args.home:
            print(conan_env.get_conan_home_path())
        if args.version:
            print(conan_env.get_conan_version())
    elif args.subparser_name == 'build':
        host_profile = f"{utils.get_profiles_dir()}/{args.profile_host}.profile"

        if not os.path.isfile(host_profile):
            raise RuntimeError(f'Host profile {host_profile} does not exist')

        if not args.profile_build:
            args.profile_build = args.profile_host

        build_profile = f"{utils.get_profiles_dir()}/{args.profile_build}.profile"

        if not os.path.isfile(build_profile):
            raise RuntimeError(f'Build profile {build_profile} does not exist')

        path = args.path if args.path else utils.get_recipes_dir()

        conan.build_packages(
            path,
            args.package, args.version,
            host_profile, build_profile, args.export_recipes)
    elif args.subparser_name == 'clean':
        conan.clean()
    else:
        conan.execute_conan_command(args.path if args.path else utils.get_recipes_dir(), args.subparser_name, args.all)


