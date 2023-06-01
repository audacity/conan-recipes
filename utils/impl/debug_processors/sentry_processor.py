import subprocess
import os
import sys
import shutil
import re

from pathlib import Path

from impl.debug_processor import DebugProcessor, register_debug_processor
from impl.package_reference import PackageReference
from impl.config import directories
from impl.files import safe_rm_tree

class SentryProcessor(DebugProcessor):
    def __init__(self, skip_upload:bool):
        self.skip_upload = skip_upload

    def activate(self, directory:str=None):
        try:
            subprocess.check_output(['sentry-cli', '--version'])
        except FileNotFoundError:
            print('sentry-cli not found, skipping')
            return False

        self.sentry_host = os.environ.get('SENTRY_HOST')
        if not self.sentry_host:
            print('SENTRY_HOST not set, skipping')
            return False

        if not self.sentry_host.startswith('http'):
            self.sentry_host = 'https://' + self.sentry_host

        self.sentry_auth_token = os.environ.get('SENTRY_AUTH_TOKEN')
        if not self.sentry_auth_token:
            print('SENTRY_AUTH_TOKEN not set, skipping')
            return False

        self.sentry_org = os.environ.get('SENTRY_ORG_SLUG')
        if not self.sentry_org:
            print('SENTRY_ORG_SLUG not set, skipping')
            return False

        self.sentry_project = os.environ.get('SENTRY_PROJECT_SLUG')
        if not self.sentry_project:
            print('SENTRY_PROJECT_SLUG not set, skipping')
            return False

        if directory:
            self.sentry_dir = directory
        else:
            self.sentry_dir = os.path.join(directories.temp_dir, 'debug_processors', 'sentry')

        return True

    def __upload_to_sentry(self, path: str):
        for i in range(3):
            try:
                subprocess.check_call([
                    'sentry-cli', '--auth-token', self.sentry_auth_token,
                    '--url', self.sentry_host,
                    'upload-dif', path,
                    '--org', self.sentry_org,
                    '--project', self.sentry_project,
                    '--include-sources',
                    '--log-level=info',
                ])
                break
            except subprocess.CalledProcessError as e:
                print('sentry-cli failed with exit code', e.returncode)
                print('retrying...')
                import time
                time.sleep(5 * (i + 1))

    def __create_source_bundle(self, debug_file:str):
        try:
            subprocess.check_call(['sentry-cli', 'debug-files', 'bundle-sources', debug_file])
        except subprocess.CalledProcessError as e:
            print('`sentry-cli debug-files bundle-sources` failed with exit code', e.returncode)

    def __process_binutils(self, build_dir: str, output_dir: str):
        for path in Path(build_dir).rglob('*.so*'):
            if path.is_symlink() or path.is_dir():
                continue
            output_file = os.path.join(output_dir, path.name)
            shutil.copy2(path, os.path.join(output_dir, path.name))
            try:
                subprocess.check_call(['objcopy', '--only-keep-debug', output_file, output_file + '.debug'])
                subprocess.check_call(['objcopy', '--strip-debug', output_file])
                subprocess.check_call(['objcopy', '--add-gnu-debuglink=' + output_file + '.debug', output_file])
                self.__create_source_bundle(output_file + '.debug')
            except subprocess.CalledProcessError as e:
                print('objcopy failed with exit code', e.returncode)

    def __process_dsymutil(self, build_dir: str, output_dir: str):
        for path in Path(build_dir).rglob('*.dylib*'):
            if path.is_symlink():
                continue
            output_file = os.path.join(output_dir, path.name)
            shutil.copy2(path, os.path.join(output_dir, path.name))
            try:
                subprocess.check_call(['dsymutil', '-o', output_file + '.dSYM', output_file])
                self.__create_source_bundle(output_file + '.dSYM')
            except subprocess.CalledProcessError as e:
                print('dsymutil failed with exit code', e.returncode)


    def __process_pdbs(self, build_dir: str, output_dir: str):
        for path in Path(build_dir).rglob('*.pdb'):
            if re.fullmatch(r'vc[0-9]+\.pdb', path.name):
                continue

            output_file = os.path.join(output_dir, path.name)
            try:
                shutil.copy2(path, output_file)
                self.__create_source_bundle(output_file)
            except subprocess.CalledProcessError as e:
                print('sentry-cli failed with exit code', e.returncode)
            except Exception as e:
                print(f'Failed to copy {path} to {output_file}: {e}')

        for path in Path(build_dir).rglob('*.dll'):
            output_file = os.path.join(output_dir, path.name)
            try:
                shutil.copy2(path, output_file)
            except Exception as e:
                print(f'Failed to copy {path} to {output_file}: {e}')

    def process(self, package_reference:PackageReference, source_dir: str, build_dir: str):
        print('Discovering debug symbols for', package_reference)

        temp_dir = os.path.join(self.sentry_dir, package_reference.name, package_reference.version)
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        try:
            if sys.platform == 'win32':
                self.__process_pdbs(build_dir, temp_dir)
            elif sys.platform == 'darwin':
                self.__process_dsymutil(build_dir, temp_dir)
            else:
                self.__process_binutils(build_dir, temp_dir)
        except subprocess.CalledProcessError as e:
            print('sentry-cli failed with exit code', e.returncode)

    def finalize(self):
        if self.skip_upload:
            return
        self.__upload_to_sentry(self.sentry_dir)
        safe_rm_tree(self.sentry_dir)

    def discard(self):
        print('Discarding debug symbols for Sentry')
        safe_rm_tree(self.sentry_dir)

register_debug_processor('sentry', lambda skip_upload: SentryProcessor(skip_upload))
