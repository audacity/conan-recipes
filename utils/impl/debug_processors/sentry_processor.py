import subprocess
import os
import re

from pathlib import Path

from impl.debug_processor import DebugProcessor, register_debug_processor
from impl.package_reference import PackageReference

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

    def process(self, package_reference:PackageReference, source_dir: str, build_dir: str):
        for i in range(3):
            try:
                subprocess.check_call([
                    'sentry-cli', '--auth-token', self.sentry_auth_token,
                    '--url', self.sentry_host,
                    'upload-dif', build_dir,
                    '--org', self.sentry_org,
                    '--project', self.sentry_project,
                    '--include-sources',
                    '--log-level=info',
                ])
            except subprocess.CalledProcessError as e:
                print('sentry-cli failed with exit code', e.returncode)
                print('retrying...')
                import time
                time.sleep(5 * (i + 1))
                continue

    def finalize(self):
        pass

register_debug_processor('sentry', lambda: SentryProcessor())
