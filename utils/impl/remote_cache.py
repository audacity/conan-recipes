import os
import tarfile

from impl.config import directories
from impl.arifactory import ArtifactoryInstance
from impl.files import safe_rm_tree
from impl.conan_env import ConanEnv
from impl.upload import upload_all
from impl.debug_processor import create_debug_processor

def get_artifactory(remote:str, username:str, password:str, key:str):
    if not remote:
        remote = os.environ.get('ARTIFACTORY_CACHE_URL', None)
        if not remote:
            raise Exception("No remote specified and ARTIFACTORY_CACHE_URL is not set")

    return ArtifactoryInstance(remote, username=username, password=password, key=key)

def get_cache_file_name(cache_id:str, compression:str='xz'):
    return f'{cache_id}.tar.{compression}' if compression != 'none' else f'{cache_id}.tar'

def upload_cache(remote:str, username:str, password:str, key:str, group_id:str, cache_id:str, compression:str='xz'):
    cache_file_name = get_cache_file_name(cache_id, compression=compression)
    temp_cache_path = os.path.join(directories.temp_dir, f'{cache_file_name}')

    os.makedirs(directories.temp_dir, exist_ok=True)

    if os.path.exists(cache_file_name):
        os.unlink(cache_file_name)

    with tarfile.open(temp_cache_path, f'w:{compression}' if compression != 'none' else 'w') as tar:
        print(f'Adding {directories.conan_home_dir} to {temp_cache_path}')
        tar.add(directories.conan_home_dir, arcname='conan')
        debug_symbols_dir = os.path.join(directories.temp_dir, 'debug_processors')
        if os.path.exists(debug_symbols_dir):
            print(f'Adding {debug_symbols_dir} to {temp_cache_path}')
            tar.add(debug_symbols_dir, arcname='debug_processors')

    try:
        print(f'Uploading {temp_cache_path} to {remote}')
        artifactoy = get_artifactory(remote, username=username, password=password, key=key)
        uri = artifactoy.upload_file(f'{group_id}/{cache_file_name}', temp_cache_path)
        print(f'Uploaded {temp_cache_path} to {uri}')
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


def process_cache(remote:str, username:str, password:str, key:str, group_id:str, recipes_remote:str, binaries_remote:str):
    artifactory = get_artifactory(remote, username=username, password=password, key=key)
    entries = artifactory.list_files(group_id)

    for entry in entries:
        local_path = os.path.join(directories.temp_dir, entry)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        print(f'Downloading {entry} to {local_path}')
        artifactory.get_file(entry, local_path)
        old_conan_home_dir = os.path.join(directories.conan_home_dir)
        cache_dir = os.path.join(directories.temp_dir, 'remote_cache', group_id)

        try:
            with tarfile.open(local_path, 'r') as tar:
                print(f'Extracting {local_path} to {cache_dir}')
                tar.extractall(path=cache_dir)

            directories.conan_home_dir = os.path.join(cache_dir, 'conan')

            with ConanEnv():
                upload_all(recipes_remote, binaries_remote)

            debug_dir = os.path.join(cache_dir, 'debug_processors')

            if os.path.exists(debug_dir):
                print(f'Processing debug symbols in {debug_dir}')
                for entry in os.listdir(debug_dir):
                    debug_processor = create_debug_processor(entry, False)
                    if debug_processor.activate(os.path.join(debug_dir, entry)):
                        debug_processor.finalize()
        finally:
            directories.conan_home_dir = old_conan_home_dir
            safe_rm_tree(cache_dir)
            os.unlink(local_path)
