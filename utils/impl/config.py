import os
import sys
from functools import cache
import pathlib

@cache
class Directories():
    root_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', '..'))

    output_dir = os.path.join(os.getcwd(), '.conan_utils')
    env_dir = os.path.join(os.getcwd(), '.conan_utils', 'venv')
    conan_home_dir = os.path.join(os.getcwd(), '.conan_utils', 'conan')
    temp_dir = os.path.join(os.getcwd(), '.conan_utils', 'temp')

    build_dir = os.path.join(temp_dir, 'build')

    config_dir = os.path.join(root_dir, 'config')
    recipes_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', '..', 'recipes'))

    install_dir = os.path.join(output_dir, 'install')

    @property
    def config_packages_dir(self):
        return os.path.join(self.config_dir, 'packages')

    @property
    def config_platform_packages_dir(self):
        return os.path.join(self.config_packages_dir, sys.platform.lower())

    @property
    def profiles_dir(self):
        return os.path.join(self.config_dir, 'profiles')

    def change_output_dir(self, output_dir:str):
        self.output_dir = output_dir
        self.env_dir = os.path.join(output_dir, 'venv')
        self.conan_home_dir = os.path.join(output_dir, 'conan')
        self.temp_dir = os.path.join(output_dir, 'temp')
        self.build_dir = os.path.join(self.temp_dir, 'build')

    def force_short_paths(self):
        drive = pathlib.Path(Directories.output_dir).drive + '\\'

        if not drive:
            return

        self.output_dir = os.path.join(drive, 't')
        self.env_dir = os.path.join(self.output_dir, 'v')
        self.conan_home_dir = os.path.join(self.output_dir, 'c')
        self.temp_dir = os.path.join(self.output_dir, 't')
        self.build_dir = os.path.join(self.temp_dir, 'b')
        self.install_dir = os.path.join(self.temp_dir, 'i')

directories = Directories()
