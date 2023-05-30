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
    def activate(self):
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

    def __process_binutils(self, build_dir: str, output_dir: str):
        for path in Path(build_dir).rglob('*.so*'):
            if path.is_symlink():
                continue
            output_file = os.path.join(output_dir, path.name)
            shutil.copy2(path, os.path.join(output_dir, path.name))
            try:
                subprocess.check_call(['objcopy', '--only-keep-debug', output_file, output_file + '.debug'])
                subprocess.check_call(['objcopy', '--strip-debug', output_file])
                subprocess.check_call(['objcopy', '--add-gnu-debuglink=' + output_file + '.debug', output_file])
            except subprocess.CalledProcessError as e:
                print('objcopy failed with exit code', e.returncode)
                continue

    def __process_dsymutil(self, build_dir: str, output_dir: str):
        for path in Path(build_dir).rglob('*.dylib*'):
            if path.is_symlink():
                continue
            output_file = os.path.join(output_dir, path.name)
            shutil.copy2(path, os.path.join(output_dir, path.name))
            try:
                subprocess.check_call(['dsymutil', '-o', output_file + '.dSYM', output_file])
            except subprocess.CalledProcessError as e:
                print('dsymutil failed with exit code', e.returncode)
                continue

    def __process_pdbs(self, build_dir: str, output_dir: str):
        for path in Path(build_dir).rglob('*.pdb'):
            if re.fullmatch(r'vc[0-9]+\.pdb', path.name):
                continue

            output_file = os.path.join(output_dir, path.name)
            shutil.copy2(path, output_file)

        for path in Path(build_dir).rglob('*.dll'):
            output_file = os.path.join(output_dir, path.name)
            shutil.copy2(path, output_file)

    def process(self, package_reference:PackageReference, source_dir: str, build_dir: str):
        print('Uploading debug symbols for', package_reference)

        temp_dir = os.path.join(directories.temp_dir, 'sentry', package_reference.name, package_reference.version)
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        try:
            if sys.platform == 'win32':
                self.__process_pdbs(build_dir, temp_dir)
            elif sys.platform == 'darwin':
                self.__process_dsymutil(build_dir, temp_dir)
            else:
                self.__process_binutils(build_dir, temp_dir)

            # Upload temp_dir to sentry
            self.__upload_to_sentry(temp_dir)
        finally:
            safe_rm_tree(temp_dir)

    def finalize(self):
        safe_rm_tree(os.path.join(directories.temp_dir, 'sentry'))

register_debug_processor('sentry', lambda: SentryProcessor())