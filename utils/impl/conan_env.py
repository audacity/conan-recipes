import venv
import os
import subprocess
from impl import utils
from impl.config import directories
import shutil


class ConanEnv:
    old_env_path = None
    old_home_path = None

    def __init__(self, env_path=None, home_path=None):
        self.env_path = env_path

        if not self.env_path:
            expected_path = directories.env_dir
            if os.path.exists(expected_path):
                self.env_path = expected_path
            else:
                print("Using system Python")

        self.home_path = home_path

        if not self.home_path:
            expected_path = directories.conan_home_dir
            if os.path.exists(expected_path):
                self.home_path = expected_path
            else:
                print("Using system Conan home")

    def __enter__(self):
        print(f"Using Conan environment at {self.env_path}")
        if self.env_path and 'VIRTUAL_ENV' in os.environ:
            self.old_env_path = os.environ['VIRTUAL_ENV']

        if self.home_path and 'CONAN_HOME' in os.environ:
            self.old_home_path = os.environ['CONAN_HOME']

        if self.env_path:
            os.environ['VIRTUAL_ENV'] = self.env_path
        if self.home_path:
            os.environ['CONAN_HOME'] = self.home_path

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.env_path:
            if self.old_env_path:
                os.environ['VIRTUAL_ENV'] = self.old_env_path
            else:
                del os.environ['VIRTUAL_ENV']

        if self.home_path:
            if self.old_home_path:
                os.environ['CONAN_HOME'] = self.old_home_path
            else:
                del os.environ['CONAN_HOME']


class ConanEnvBuilder(venv.EnvBuilder):
    def post_setup(self, context):
        with ConanEnv(context.env_dir):
            cmd = [utils.get_python(), '-m', 'pip', 'install', 'conan']
            subprocess.check_call(cmd)


def create_conan_environment(clean=False):
    env_path = directories.env_dir

    if os.path.exists(env_path):
        if not clean:
            raise RuntimeError(f"Conan environment already exists at {env_path}")

        print(f"Removing Conan environment at {env_path}")
        shutil.rmtree(env_path)

    home_path = directories.conan_home_dir

    if not os.path.exists(home_path):
        os.makedirs(home_path, exist_ok=True)

    print(f"Creating Conan environment at {env_path}, home at {home_path}")
    builder = ConanEnvBuilder(with_pip=True)
    builder.create(env_path)


def get_conan_path():
    with ConanEnv():
        return utils.get_conan()


def get_conan_home_path():
    with ConanEnv():
        if 'CONAN_HOME' in os.environ:
            return os.environ['CONAN_HOME']
        else:
            return os.path.join(os.path.expanduser('~'), '.conan2')


def get_conan_version():
    with ConanEnv():
        cmd = [utils.get_conan(), '--version']
        version_string = subprocess.check_output(cmd).decode('utf-8').strip()
        return version_string.split(' ')[-1]
