import os
import sys
import sqlite3
import tarfile

from pathlib import Path

import yaml

from impl.config import directories
from impl.artifactory import ArtifactoryInstance
from impl.files import safe_rm_tree
from impl.conan_env import ConanEnv
from impl.upload import upload_all
from impl.debug_processor import create_debug_processor, load_processors
from impl.build_order import get_build_order

def get_artifactory(remote:str, username:str, password:str, key:str):
    if not remote:
        remote = os.environ.get('ARTIFACTORY_CACHE_URL', None)
        if not remote:
            raise Exception("No remote specified and ARTIFACTORY_CACHE_URL is not set")

    return ArtifactoryInstance(remote, username=username, password=password, key=key)


def get_cache_file_name(cache_id:str, compression:str='xz'):
    return f'{cache_id}.tar.{compression}' if compression != 'none' else f'{cache_id}.tar'


def __add_metadata(tar:tarfile.TarFile, metadata_file:str):
    if metadata_file:
        if not os.path.exists(metadata_file):
            raise Exception(f'Metadata file {metadata_file} does not exist')
        tar.add(metadata_file, arcname='metadata.yml')


def upload_cache(remote:str, username:str, password:str, key:str, group_id:str, cache_id:str, compression:str='xz', metadata_file:str=None):
    cache_file_name = get_cache_file_name(cache_id, compression=compression)
    temp_cache_path = os.path.join(directories.temp_dir, cache_file_name)

    os.makedirs(directories.temp_dir, exist_ok=True)

    if os.path.exists(cache_file_name):
        os.unlink(cache_file_name)

    tar_mode = f'w:{compression}' if compression != 'none' else 'w'

    with tarfile.open(temp_cache_path, tar_mode) as tar:
        print(f'Adding {directories.conan_home_dir} to {temp_cache_path}')
        tar.add(directories.conan_home_dir, arcname='conan')
        __add_metadata(tar, metadata_file)

    temp_debug_path = os.path.join(directories.temp_dir, f'debug_{cache_file_name}')
    debug_symbols_dir = os.path.join(directories.temp_dir, 'debug_processors')
    if os.path.exists(debug_symbols_dir):
        with tarfile.open(temp_debug_path, tar_mode) as tar:
            print(f'Adding {debug_symbols_dir} to {temp_cache_path}')
            tar.add(debug_symbols_dir, arcname='debug_processors')
            __add_metadata(tar, metadata_file)

    try:
        artifactoy = get_artifactory(remote, username=username, password=password, key=key)
        print(f'Uploading {temp_cache_path} to {remote}')
        uri = artifactoy.upload_file(f'{group_id}/conan/{sys.platform.lower()}/{cache_file_name}', temp_cache_path)
        print(f'Uploaded {temp_cache_path} to {uri}')

        if os.path.exists(temp_debug_path):
            print(f'Uploading {temp_debug_path} to {remote}')
            uri = artifactoy.upload_file(f'{group_id}/debug/{sys.platform.lower()}/{cache_file_name}', temp_debug_path)
            print(f'Uploaded {temp_debug_path} to {uri}')
    finally:
        if os.path.exists(temp_cache_path):
           os.unlink(temp_cache_path)


def delete_cache(remote:str, username:str, password:str, key:str, group_id:str, cache_id:str, compression:str='xz'):
    artifactory = get_artifactory(remote, username=username, password=password, key=key)
    if cache_id:
        artifactory.delete_uri(f'{group_id}/{get_cache_file_name(cache_id, compression=compression)}')
    else:
        artifactory.delete_uri(group_id)


def list_cache(remote:str, username:str, password:str, key:str, group_id:str):
    artifactory = get_artifactory(remote, username=username, password=password, key=key)
    return artifactory.list_files(group_id)

def __fix_win_cache_for_upload(conan_home_dir:str):
    print(f'Fixing win cache for upload', flush=True)
    db_path = os.path.join(conan_home_dir, 'p', 'cache.sqlite3')

    con = sqlite3.connect(db_path)

    try:
        con.execute('UPDATE packages SET path = REPLACE(path, \'\\\', \'/\')')
        con.commit()
    finally:
        con.close()

def __process_cache(artifactory:ArtifactoryInstance, path_prefix:str, entry_handler:callable):
    entries = artifactory.list_files(path_prefix)

    for entry in entries:
        local_path = os.path.join(directories.temp_dir, entry)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        print(f'Downloading {entry} to {local_path}', flush=True)
        artifactory.get_file(entry, local_path)

        cache_dir = os.path.join(directories.temp_dir, 'remote_cache', path_prefix, Path(entry).stem)

        try:
            with tarfile.open(local_path, 'r') as tar:
                print(f'Extracting {local_path} to {cache_dir}', flush=True)
                tar.extractall(path=cache_dir)

            entry_handler(cache_dir)
        finally:
            safe_rm_tree(cache_dir)
            os.unlink(local_path)

class __Metadata:
    upload_build_tools = False
    build_order = None
    platform = None

    def __init__(self, cache_dir):
        metadate_file_path = os.path.join(cache_dir, 'metadata.yml')

        if not os.path.exists(metadate_file_path):
            return

        with open(metadate_file_path, 'r') as f:
            metadata = yaml.safe_load(f)

        if not metadata:
            return

        self.upload_build_tools = metadata.get('upload_build_tools', self.upload_build_tools)
        self.build_order = metadata.get('build_order', self.build_order)
        self.platform = metadata.get('platform', self.platform)

    @property
    def platform_is_win32(self):
        return self.platform and self.platform == 'win32'

def process_conan_cache(remote:str, username:str, password:str, key:str, group_id:str, recipes_remote:str, binaries_remote:str):
    def process(cache_dir:str):
        try:
            old_conan_home_dir = directories.conan_home_dir
            directories.conan_home_dir = os.path.join(cache_dir, 'conan')
            with ConanEnv():
                metadata = __Metadata(cache_dir)

                if metadata.platform_is_win32 and sys.platform.lower() != 'win32':
                    __fix_win_cache_for_upload(directories.conan_home_dir)

                upload_all(
                    recipes_remote, binaries_remote,
                    metadata.upload_build_tools,
                    get_build_order(metadata.build_order, metadata.platform))
        finally:
            directories.conan_home_dir = old_conan_home_dir

    artifactory = get_artifactory(remote, username=username, password=password, key=key)
    __process_cache(artifactory, f'{group_id}/conan', process)


def process_debug_cache(remote:str, username:str, password:str, key:str, group_id:str):
    load_processors()

    def process(cache_dir:str):
        debug_dir = os.path.join(cache_dir, 'debug_processors')

        if not os.path.exists(debug_dir):
            return

        print(f'Processing debug symbols in {debug_dir}')
        for entry in os.listdir(debug_dir):
            try:
                print(f'Activating debug processor {entry}...', flush=True)
                debug_processor = create_debug_processor(entry, False)
                if debug_processor.activate(os.path.join(debug_dir, entry)):
                    print(f'Processing using debug processor {entry}...', flush=True)
                    debug_processor.finalize()
            except Exception as e:
                print(f'Error processing debug symbols in {entry}: {e}', flush=True)

    artifactory = get_artifactory(remote, username=username, password=password, key=key)
    __process_cache(artifactory, f'{group_id}/debug/{sys.platform.lower()}', process)
