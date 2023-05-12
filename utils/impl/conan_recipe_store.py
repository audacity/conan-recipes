import os
import yaml
import subprocess
from impl import conan_env
from impl import utils
from impl import package_config
from impl import debug

class ConanRecipeStore:
    versions = None
    __commands_map = {
        'export-recipes': ('export_all', 'export'),
        'update-sources': ('source_all', 'source'),
    }

    @property
    def name(self):
        return os.path.basename(self.path)

    def __init__(self, path: str):
        if not os.path.exists(path):
            raise RuntimeError(f"Path `{path}` does not exist")

        self.path = path

        config_path = os.path.join(path, 'config.yml')

        if not os.path.exists(config_path):
            raise RuntimeError(f"Config `{path}` does not exist")

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            self.versions = config['versions']

    def get_recipe_folder(self, version:str):
        if not version in self.versions:
            raise RuntimeError(f"Version `{version}` not found. {', '.join(self.versions.keys())} available for {self.name}")

        recipe_folder = os.path.join(self.path, self.versions[version]['folder'])

        if not os.path.exists(recipe_folder):
            raise RuntimeError(f"Recipe folder `{recipe_folder}` does not exist")

        return recipe_folder

    def get_source_folder(self, version):
        return os.path.join(self.get_recipe_folder(version), "src")

    def get_build_folder(self, version):
        return os.path.join(self.get_recipe_folder(version), "build")

    def export(self, version:str):
        config = package_config.PackageConfig()

        with conan_env.ConanEnv():
            cmd = [
                utils.get_conan(), 'export', self.get_recipe_folder(version),
                '--version', version,
                '--user', config.get_package_user(self.name, version),
                '--channel', config.get_package_channel(self.name, version),
                '--no-remote'
            ]

            subprocess.check_call(cmd)

    def export_all(self):
        for version in self.versions.keys():
            self.export(version)

    def source(self, version):
        config = package_config.PackageConfig()

        with conan_env.ConanEnv():
            cmd = [
                utils.get_conan(), 'source', self.get_recipe_folder(version),
                '--version', version,
                '--user', config.get_package_user(self.name, version),
                '--channel', config.get_package_channel(self.name, version)
            ]

            subprocess.check_call(cmd)

    def source_all(self):
        for version in self.versions.keys():
            self.source(version)

    def execute_command(self, command, all):
        if all:
            getattr(self, self.__commands_map[command][0])()
        else:
            config = package_config.PackageConfig()
            name = os.path.basename(self.path)
            pkg_conf = config.get_package_config(name)
            if pkg_conf:
                getattr(self, self.__commands_map[command][1])(pkg_conf['version'])

    def build(self, package:str, version:str, host_profile:str=None, build_profile:str=None):
        config = package_config.PackageConfig()
        pkg_config = config.get_package_config(package)

        if not pkg_config:
            raise RuntimeError(f"Config for package `{package}` not found")

        user = config.get_package_user(package, version)
        channel = config.get_package_channel(package, version)

        is_build_tool = 'build_tool' in pkg_config and pkg_config['build_tool']

        if is_build_tool:
            if not build_profile:
                raise RuntimeError(f"Build profile is required for build tool `{package}`")
            host_profile = build_profile
        elif not build_profile:
            build_profile = host_profile

        print(f"Building `{package}/{version}@{user}/{channel}`...")

        with conan_env.ConanEnv():
            cmd = [
                utils.get_conan(), 'install',
                '--version', version,
                '--user', user,
                '--channel', channel,
                '--no-remote',
                '-vvv',
                self.get_recipe_folder(version)
            ]

            print(cmd)

            if host_profile:
                cmd += ['-pr:h', host_profile]

            if build_profile:
                cmd += ['-pr:b', build_profile]

            if 'options' in pkg_config:
                for opt in pkg_config['options'].split():
                    cmd += ['-o:h', opt.strip()]


            print(f"== Building package...", flush=True)
            cmd[1] = 'build'
            subprocess.check_call(cmd)

            print(f"== Creating Conan package...", flush=True)
            cmd[1] = 'export-pkg'
            subprocess.check_call(cmd)




def get_recipe_store(package_name):
    return ConanRecipeStore(os.path.join(utils.get_recipes_dir(), package_name))
