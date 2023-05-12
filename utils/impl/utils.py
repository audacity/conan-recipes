import os
import sys
from functools import cache

@cache
def get_exptected_output_location():
    return os.path.join(os.getcwd(), '.conan_utils')

@cache
def get_expected_env_location():
    return os.path.join(get_exptected_output_location(), 'venv')

@cache
def get_expected_conan_home_location():
    return os.path.join(get_exptected_output_location(), 'conan')

@cache
def get_root_dir():
    return os.path.realpath(os.path.join(os.path.dirname(__file__), '..', '..'))

@cache
def get_config_dir():
    return os.path.join(get_root_dir(), 'config')

@cache
def get_config_packages_dir():
    return os.path.join(get_config_dir(), 'packages')

@cache
def get_config_platform_packages_dir():
    return os.path.join(get_config_packages_dir(), sys.platform.lower())

@cache
def get_profiles_dir():
    return os.path.join(get_config_dir(), 'profiles')

@cache
def get_recipes_dir():
    return os.path.join(get_root_dir(), 'recipes')

def get_python():
    if os.environ['VIRTUAL_ENV']:
        if sys.platform == 'win32':
            return os.path.join(os.environ['VIRTUAL_ENV'], 'Scripts', 'python.exe')
        else:
            return os.path.join(os.environ['VIRTUAL_ENV'], 'bin', 'python')
    else:
        return sys.executable


def get_conan():
    if 'VIRTUAL_ENV' in os.environ:
        if sys.platform == 'win32':
            return os.path.join(os.environ['VIRTUAL_ENV'], 'Scripts', 'conan.exe')
        else:
            return os.path.join(os.environ['VIRTUAL_ENV'], 'bin', 'conan')
    else:
        if sys.platform == 'win32':
            return 'conan.exe'
        else:
            return 'conan'
