import os
import subprocess
import json

from impl.package_config_provider import package_config_provider
from impl.package_reference import PackageReference
from impl.utils import get_conan
from impl.profiles import ConanProfiles
from impl.config import directories
from impl.debug import handle_build_completed


class ConanRecipe:
    installed_build_folders = []

    def __init__(self, recipe_dir:str, package_reference:PackageReference):
        self.recipe_dir = recipe_dir
        self.reference = package_reference
        self.config = package_config_provider.get_package_config(package_reference.name)

        if not self.config:
            raise RuntimeError(f"Package config for `{package_reference}` not found")

    @property
    def is_build_tool(self):
        return 'build_tool' in self.config and self.config['build_tool']

    @property
    def is_python_require(self):
        return 'python_require' in self.config and self.config['python_require']

    @property
    def local_source_dir(self):
        return os.path.join(self.recipe_dir, 'src')

    @property
    def test_package_dir(self):
        return os.path.join(self.recipe_dir, 'test_package')

    @property
    def local_build_dirs(self):
        return [
            os.path.join(self.recipe_dir, 'build'),
            os.path.join(self.recipe_dir, 'build-debug'),
            os.path.join(self.recipe_dir, 'build-release'),
            os.path.join(self.recipe_dir, 'build-relwithdebinfo'),
            os.path.join(self.recipe_dir, 'build-minsizerel'),
        ] + self.installed_build_folders

    @property
    def local_test_build_dirs(self):
        return [
            os.path.join(self.test_package_dir, 'build'),
            os.path.join(self.test_package_dir, 'build-debug'),
            os.path.join(self.test_package_dir, 'build-release'),
            os.path.join(self.test_package_dir, 'build-relwithdebinfo'),
            os.path.join(self.test_package_dir, 'build-minsizerel'),
        ]

    def export(self):
        cmd = [
            get_conan(), 'export', self.recipe_dir,
            '--version', self.reference.version,
            '--user', self.reference.user,
            '--channel', self.reference.channel,
            '--no-remote',
        ]

        subprocess.check_call(cmd)

    def source(self):
        cmd = [
            get_conan(), 'source', self.recipe_dir,
            '--version', self.reference.version,
            '--user', self.reference.user,
            '--channel', self.reference.channel,
        ]

        subprocess.check_call([get_conan(), '--version'])
        subprocess.check_call(cmd)

    def __run_build_command(self, cmd:str, profiles:ConanProfiles, remotes:list[str] = None, additional_options:list[str] = None, include_recipe=True):
        cmd = [
            get_conan(), cmd,
            '--version', self.reference.version,
            '--user', self.reference.user,
            '--channel', self.reference.channel,
            '-vvv',
            '-pr:h', profiles.get_profile(self.is_build_tool),
            '-pr:b', profiles.build_profile,
        ]

        if 'options' in self.config:
            for opt in self.config['options'].split():
                cmd += ['-o:h', opt.strip()]

        if additional_options:
            cmd += additional_options

        if remotes and len(remotes) > 0:
            for remote in remotes:
                cmd += ['-r', remote]
        else:
            cmd += ['--no-remote']

        if include_recipe:
            cmd += [self.recipe_dir]

        print(cmd)
        subprocess.check_call(cmd)

    def install_dependecies(self, profiles:ConanProfiles, remotes:list[str] = None, build_missing:bool = False):
        print(f"Installing dependencies for `{self.reference}`...", flush=True)
        additional_options = ['--build', 'missing'] if build_missing else None
        self.__run_build_command('install', profiles, remotes, additional_options)


    def build(self, profiles:ConanProfiles):
        if self.is_python_require:
            print(f"Skipping build for python_require package `{self.reference}`")
            return

        print(f"Building `{self.reference}`...")

        self.install_dependecies(profiles)

        print(f"== Building package...", flush=True)
        self.__run_build_command('build', profiles)

        print(f"== Creating Conan package...", flush=True)
        self.__run_build_command('export-pkg', profiles)

        handle_build_completed(self.reference, self.local_source_dir, self.local_build_dirs)

    def __get_package_id(self, install_output:bytes):
        try:
            nodes = json.loads(install_output)['graph']['nodes']

            for node in nodes.values():
                if str(self.reference) in node['ref']:
                    return node['package_id']

            return None
        except:
            return None

    def __get_build_folder(self, package_id:str):
        try:
            return subprocess.check_output([
                get_conan(), 'cache', 'path', f'{self.reference}:{package_id}', '--folder=build'
                ]).decode('utf-8').strip()
        except subprocess.CalledProcessError:
            return None

    def __get_cache_source_folder(self, package_id:str):
        try:
            return subprocess.check_output([
                get_conan(), 'cache', 'path', f'{self.reference}', '--folder=source'
                ]).decode('utf-8').strip()
        except subprocess.CalledProcessError:
            return None

    def install(self, profiles:ConanProfiles, remotes:list[str] = None, build_missing:bool = False):
        print(f"Installing `{self.reference}`...", flush=True)

        cmd = [
            get_conan(), 'install',
            '-of', directories.install_dir,
            '--tool-requires' if self.is_build_tool else '--requires', str(self.reference),
            '-vvv',
            '-pr:h', profiles.host_profile,
            '-pr:b', profiles.build_profile,
            '--format', 'json'
        ]

        if build_missing:
            cmd += ['--build', 'missing']

        if remotes and len(remotes) > 0:
            for remote in remotes:
                cmd += ['-r', remote]
        else:
            cmd += ['--no-remote']

        if 'options' in self.config:
            for opt in self.config['options'].split():
                cmd += ['-o:h', opt.strip()]

        package_id = self.__get_package_id(subprocess.check_output(cmd))
        print(F'Package ID: {package_id}')
        if package_id:
            build_folder = self.__get_build_folder(package_id)
            if build_folder:
                print(F'Build folder: {build_folder}')
                self.installed_build_folders.append(build_folder)
                handle_build_completed(self.reference, self.__get_cache_source_folder(package_id), build_folder)

    def execute_command(self, command:str):
        if command == 'export-recipes':
            self.export()
        elif command == 'update-sources':
            self.source()
