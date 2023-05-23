import os
import sys
from functools import cache

@cache
class Directories():
    root_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', '..'))

    output_dir = os.path.join(os.getcwd(), '.conan_utils')
    env_dir = os.path.join(os.getcwd(), '.conan_utils', 'venv')
    conan_home_dir = os.path.join(os.getcwd(), '.conan_utils', 'conan')
    temp_dir = os.path.join(os.getcwd(), '.conan_utils', 'temp')

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

directories = Directories()
