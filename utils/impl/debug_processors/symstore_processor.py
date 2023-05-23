import os
import sys
import re

from pathlib import Path
from requests import Session

from symstore import Store, cab

from impl.debug_processor import DebugProcessor, register_debug_processor
from impl.package_reference import PackageReference
from impl.config import directories
from impl.files import safe_rm_tree
from impl.net import BearerAuth

class SymstoreProcessor(DebugProcessor):
    entries = []

    def activate(self):
        if sys.platform != 'win32':
            return False

        self.symstore_url = os.environ.get('ARTIFACTORY_SYMBOLS_URL', None)
        self.symstore_key = os.environ.get('ARTIFACTORY_SYMBOLS_KEY', os.environ.get('ARTIFACTORY_API_KEY', None))

        if not self.symstore_url:
            print('SymstoreProcessor not activated: ARTIFACTORY_SYMBOLS_URL is not set')
            return False

        if not self.symstore_key:
            print('SymstoreProcessor not activated: ARTIFACTORY_SYMBOLS_KEY or ARTIFACTORY_API_KEY is not set')
            return False

        self.session = Session()
        self.session.auth = BearerAuth(self.symstore_key)

        self.symstore_dir = os.path.join(directories.temp_dir, 'debug_processors', 'symstore')
        if not os.path.exists(self.symstore_dir):
            os.makedirs(self.symstore_dir)

        _000admin = os.path.join(self.symstore_dir, '000Admin')
        if not os.path.exists(_000admin):
            os.makedirs(_000admin)

        for file in ('000Admin/lastid.txt', '000Admin/history.txt', '000Admin/server.txt'):
            self.__download_file(file)

        self.symstore = Store(self.symstore_dir)

        print('SymstoreProcessor activated')
        return True

    def process(self, package_reference:PackageReference, source_dir: str, build_dir: str):
        transaction = self.symstore.new_transaction(package_reference.name, package_reference.version, None)

        for path in Path(build_dir).rglob('*.pdb'):
            if re.fullmatch(r'vc[0-9]+\.pdb', path.name):
                continue
            entry = transaction.new_entry(path, cab.compress)
            if entry.exists():
                continue
            print(f'Adding {path} to symstore')
            transaction.add_entry(entry)
            self.entries.append(entry)

        if len(transaction.entries) > 0:
            self.symstore.commit(transaction)

    def finalize(self):
        for entry in self.entries:
            entry_path = os.path.join(self.symstore_dir, entry.file_name, entry.file_hash)
            for file in os.listdir(entry_path):
                self.__upload_file(f'{entry.file_name}/{entry.file_hash}/{file}', os.path.join(entry_path, file))
        safe_rm_tree(self.symstore_dir)

    def __download_file(self, file:str):
        response = self.session.get(f'{self.symstore_url}/{file}', stream=True, allow_redirects=True)
        if response.status_code != 200:
            return None

        with open(os.path.join(self.symstore_dir, file), 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

    def __upload_file(self, file:str, path:str):
        print(f'Uploading {file} to remote symstore')
        with open(path, 'rb') as f:
            response = self.session.put(f'{self.symstore_url}/{file}', data=f, headers={'Content-Type': 'application/octet-stream'})
            if response.status_code != 201:
                print(f'Failed to upload {file}: {response.status_code} {response.text}')


register_debug_processor('symstore', lambda: SymstoreProcessor())
