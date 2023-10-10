import os
import sys

from functools import cache

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
