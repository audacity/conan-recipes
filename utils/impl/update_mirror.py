import os
import yaml

from requests import get
from hashlib import sha256

from impl.artifactory import ArtifactoryInstance

from impl.config import directories
from impl.conan_recipe_store import get_recipe_stores
from impl.files import safe_rm_tree


class SourcesElement:
    def __init__(self, key:str, url_key:str, urls:list, checksum:str):
        self.key = key
        self.url_key = url_key
        self.urls = urls if type(urls) is list else [urls]
        self.checksum = checksum

    def __repr__(self):
        return f"SourcesElement(key={self.key}, urls={self.urls}, checksum={self.checksum})"

    def has_mirror_url(self, mirror:str):
        for url in self.urls:
            if url.startswith(mirror):
                return True
        return False

def get_sources_element(version_sources:dict) -> list[SourcesElement]:
    if not 'url' in version_sources and not 'urls' in version_sources:
        result = []
        for key in version_sources.keys():
            source = version_sources[key]
            url_key = 'urls' if 'urls' in source else 'url'
            result.append(SourcesElement(
                key=key,
                url_key=url_key,
                urls=source[url_key],
                checksum=source['sha256'] if 'sha256' in source else None))
        return result

    url_key = 'urls' if 'urls' in version_sources else 'url'
    return [SourcesElement(
        key=None,
        url_key=url_key,
        urls=version_sources[url_key],
        checksum=version_sources['sha256'] if 'sha256' in version_sources else None)]

def download_file(name:str, version:str, url:str, checksum:str):
    try:
        response = get(url, stream=True)
        response.raise_for_status()

        filename = url.split('/')[-1]
        path = os.path.join(directories.temp_dir, name, version)

        if not os.path.exists(path):
            os.makedirs(path)

        filepath = os.path.join(path, filename)
        if os.path.exists(filepath):
            os.remove(filepath)

        hasher = sha256()
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                hasher.update(chunk)
                f.write(chunk)

        if checksum and hasher.hexdigest().lower() != checksum.lower():
            print(f"Checksum mismatch for file {filepath}, expected {checksum}, got {hasher.hexdigest()}")
            os.remove(filepath)
            return None

        return filepath
    except Exception as e:
        print(f"Failed to download file from {url}: {e}")
        return None

def download_from_mirrors(name:str, version:str, urls:list[str], checksum:str):
    for url in urls:
        filepath = download_file(name, version, url, checksum)
        if filepath:
            return filepath

    return None

def handle_single_version(name:str, conandata_path:str, version:str, remote:str, artifactory:ArtifactoryInstance):
    if not os.path.exists(conandata_path):
        print(f"Conandata `{conandata_path}` does not exist, skipping...")
        return

    print(f"Updating mirror in `{conandata_path}` for version {version}...")
    with open(conandata_path, 'r') as f:
        conandata = yaml.safe_load(f)

    if not conandata:
        print(f"Conandata is empty, skipping...")
        return

    if not 'sources' in conandata:
        print(f"Conandata does not contain sources, skipping...")
        return

    if not version in conandata['sources']:
        print(f"Conandata does not contain sources for version {version}, skipping...")
        return

    version_sources = conandata['sources'][version]

    try:
        elements = get_sources_element(version_sources)
    except Exception as e:
        print(f"Unexpected conandata fromat: {e}")
        return

    if len(elements) == 0:
        print(f"Conandata does not contain sources for version {version}, skipping...")
        return

    modified = False

    for element in elements:
        # Download the file
        path = download_from_mirrors(name, version, element.urls, element.checksum)
        if not path:
            print(f"Failed to download file for version {version}, skipping...")
            continue
        mirror_url = f'{name}/{version}/{os.path.basename(path)}'

        if not artifactory.file_exists(mirror_url):
            try:
                mirror_url = artifactory.upload_file(mirror_url, path)
            except Exception as e:
                print(f"Failed to upload file for version {version}, skipping... ({e}))")
                continue
        else:
            print(f"File already exists in mirror, skipping upload...")
            mirror_url = artifactory.get_file_url(mirror_url)

        if element.has_mirror_url(mirror_url):
            print(f"Mirror URL already exists in conandata, skipping...")
            continue

        if element.key:
            version_sources[element.key][element.url_key] = element.urls + [mirror_url]
        else:
            version_sources[element.url_key] = element.urls + [mirror_url]

        modified = True

    if not modified:
        print(f"Nothing to update, skipping...")
        return

    print(f"Updating {conandata_path}...")
    with open(conandata_path, 'w') as f:
        yaml.dump(conandata, f, sort_keys=False, width=256)


def update_mirror(remote:str, username:str, password:str, key:str, all:False):
    if not remote:
        remote = os.environ.get('ARTIFACTORY_MIRROR_URL', None)
        if not remote:
            raise Exception("No remote specified and ARTIFACTORY_MIRROR_URL is not set")

    artifactory = ArtifactoryInstance(remote, username=username, password=password, key=key)

    try:
        for recipe_store in get_recipe_stores(None, with_config_only=not all):
            if all:
                for version in recipe_store.versions.keys():
                    conandata_path = os.path.join(recipe_store.get_recipe_folder(version), 'conandata.yml')
                    handle_single_version(recipe_store.name, conandata_path, version, remote, artifactory)
            else:
                conandata_path = os.path.join(recipe_store.get_recipe_folder(recipe_store.default_version), 'conandata.yml')
                handle_single_version(recipe_store.name, conandata_path, recipe_store.default_version, remote, artifactory)
    finally:
        safe_rm_tree(directories.temp_dir)
