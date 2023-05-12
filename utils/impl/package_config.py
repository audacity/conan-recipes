import yaml
import os
import sys
from functools import cache
from impl import utils

@cache
class PackageConfig():
    __stable_packages = None
    __package_configs = {}
    __build_order = None

    def __init__(self):
        stable_packages_path = os.path.join(utils.get_config_dir(), 'stable_packages.yml')
        if os.path.exists(stable_packages_path):
            with open(stable_packages_path, 'r') as f:
                config = yaml.safe_load(f)
                self.__stable_packages = config['packages']

    def get_package_channel(self, package_name:str, package_version:str):
        if not self.__stable_packages:
            return "testing"

        if not package_name in self.__stable_packages:
            return "testing"

        package_config = self.__stable_packages[package_name]

        if type(package_config) is str:
            if package_config == "*" or package_config == package_version:
                return "stable"
            else:
                return package_version in package_config

    def get_package_user(self, package_name:str, package_version:str):
        return "audacity"


    def get_package_config(self, package_name:str):
        if not package_name in self.__package_configs:
            package_config_path = os.path.join(utils.get_config_platform_packages_dir(), f'{package_name}.yml')

            if not os.path.exists(package_config_path):
                package_config_path = os.path.join(utils.get_config_packages_dir(), f'{package_name}.yml')

            if not os.path.exists(package_config_path):
                return None

            if os.path.exists(package_config_path):
                with open(package_config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    self.__package_configs[package_name] = config['config']

        return self.__package_configs[package_name]


    def get_build_order(self):
        if self.__build_order:
            return self.__build_order

        build_order_path = os.path.join(utils.get_config_dir(), 'build_order.yml')

        if not os.path.exists(build_order_path):
            return None

        with open(build_order_path, 'r') as f:
            config = yaml.safe_load(f)['build_order']
            self.__build_order = []

            for part in config:
                build_on = part['platforms']
                if build_on == '*' or sys.platform.lower() in build_on:
                    self.__build_order += part['packages']

        return self.__build_order
