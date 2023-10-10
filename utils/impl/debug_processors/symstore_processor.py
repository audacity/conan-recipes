import os
import sys
import re

from pathlib import Path

from symstore import Store, cab

from impl.debug_processor import DebugProcessor, register_debug_processor
from impl.package_reference import PackageReference
from impl.config import directories
from impl.files import safe_rm_tree
from impl.artifactory import ArtifactoryInstance

class SymstoreProcessor(DebugProcessor):
    entries = []

    def __init__(self, skip_upload:bool):
        self.skip_upload = skip_upload


    def activate(self, directory:str=None):
        if sys.platform != 'win32':
            return False

        symstore_url = os.environ.get('ARTIFACTORY_SYMBOLS_URL', None)
        symstore_key = os.environ.get('ARTIFACTORY_SYMBOLS_KEY', os.environ.get('ARTIFACTORY_API_KEY', None))

        if not symstore_url:
            print('SymstoreProcessor not activated: ARTIFACTORY_SYMBOLS_URL is not set')
            return False

        if not symstore_key:
            print('SymstoreProcessor not activated: ARTIFACTORY_SYMBOLS_KEY or ARTIFACTORY_API_KEY is not set')
            return False

        if directory:
            self.symstore_dir = directory
        else:
            self.symstore_dir = os.path.join(directories.temp_dir, 'debug_processors', 'symstore')

        if not os.path.exists(self.symstore_dir):
            os.makedirs(self.symstore_dir)

        _000admin = os.path.join(self.symstore_dir, '000Admin')
        if not os.path.exists(_000admin):
            os.makedirs(_000admin)

        self.artifactory = ArtifactoryInstance(url=symstore_url, key=symstore_key)

        for file in ('000Admin/lastid.txt', '000Admin/history.txt', '000Admin/server.txt'):
            self.__download_file(file)

        self.symstore = Store(self.symstore_dir)

        print('SymstoreProcessor activated')
        return True

    def process(self, package_reference:PackageReference, source_dir: str, build_dir: str):
        if package_reference.is_build_tool:
            print(f'Skipping symstore upload for build tool {package_reference}')
            return

        transaction = self.symstore.new_transaction(package_reference.name, package_reference.version, None)

        for path in Path(build_dir).rglob('*.pdb'):
            if re.fullmatch(r'vc[0-9]+\.pdb', path.name):
                continue
            try:
                entry = transaction.new_entry(path, cab.compress)
            except Exception as e:
                print(f'Failed to create symstore entry for {path}: {e}')
                continue

            if entry.exists():
                continue
            print(f'Adding {path} to symstore')

            try:
                transaction.add_entry(entry)
                self.entries.append(entry)
            except Exception as e:
                print(f'Failed to add {path} to symstore: {e}')

        if len(transaction.entries) > 0:
            self.symstore.commit(transaction)

    def finalize(self):
        if self.skip_upload:
            return

        print(self.symstore.transactions.items())

        for dir in os.listdir(self.symstore_dir):
            if dir == '000Admin':
                continue
            for root, dirnames, filenames in os.walk(os.path.join(self.symstore_dir, dir)):
                relative_root = os.path.relpath(root, self.symstore_dir).replace('\\', '/')
                for filename in filenames:
                    self.__upload_file(f'{relative_root}/{filename}', os.path.join(root, filename))

        safe_rm_tree(self.symstore_dir)

    def discard(self):
        print('Discarding symstore transaction')
        safe_rm_tree(self.symstore_dir)

    def __download_file(self, file:str):
        self.artifactory.get_file(file, os.path.join(self.symstore_dir, file))

    def __upload_file(self, file:str, path:str):
        try:
            print(f'Uploading {file} to remote symstore')
            url = self.artifactory.upload_file(file, path)
        except Exception as e:
            print(f'Failed to upload {file} to remote symstore: {e}')


register_debug_processor('symstore', lambda skip_upload: SymstoreProcessor(skip_upload))
