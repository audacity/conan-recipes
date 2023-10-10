import os
from hashlib import md5, sha1, sha256

from impl.net import BearerAuth
from requests import Session


class ArtifactoryInstance:
    def __init__(self, url:str, repo:str=None, username:str=None, password:str=None, key:str=None) -> None:
        if repo:
            self.url = url
            self.repo = repo
        else:
            while len(url) > 0 and url.endswith('/'):
                url = url[:-1]
            self.url, _, self.repo = url.rpartition('/')

        self.session = Session()

        if not username:
            if not key:
                key = os.environ.get('ARTIFACTORY_API_KEY', os.environ.get('ARTIFACTORY_SYMBOLS_KEY', None))

                if not key:
                    raise RuntimeError("No username or key specified and ARTIFACTORY_API_KEY is not set")
            self.session.auth = BearerAuth(key)
        else:
            self.session.auth = (username, password)

    def upload_file(self, remote_path:str, local_path:str) -> str:
        if not os.path.isfile(local_path):
            raise FileNotFoundError(f"File {local_path} does not exist")

        sha1_hasher = sha1()
        sha256_hasher = sha256()
        md5_hasher = md5()

        with open(local_path, 'rb') as f:
            while chunk := f.read(8192):
                sha1_hasher.update(chunk)
                sha256_hasher.update(chunk)
                md5_hasher.update(chunk)

        url = f'{self.url}/{self.repo}/{remote_path}'

        with open(local_path, 'rb') as f:
            response = self.session.put(url, data=f, headers={
                'Content-Type': 'application/octet-stream',
                'X-Checksum-Sha256': sha256_hasher.hexdigest(),
                'X-Checksum-Sha1': sha1_hasher.hexdigest(),
                'X-Checksum-Md5': md5_hasher.hexdigest()})
            if response.status_code != 201:
                raise RuntimeError(f"Failed to upload file to {url}: {response.text}")
            else:
                return response.json()['downloadUri']

    def get_file_url(self, remote_path:str) -> str:
        return f'{self.url}/{self.repo}/{remote_path}' if not remote_path.startswith(self.url) else remote_path

    def file_exists(self, remote_path:str) -> bool:
        response = self.session.head(self.get_file_url(remote_path))
        return response.status_code == 200

    def get_file(self, remote_path:str, local_path:str) -> str:
        response = self.session.get(self.get_file_url(remote_path))
        if response.status_code != 200:
            raise RuntimeError(f"Failed to download file from {self.get_file_url(remote_path)}: {response.text}")

        hasher = sha256()

        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
        finally:
            pass

        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                hasher.update(chunk)
                f.write(chunk)

        return hasher.hexdigest()

    def delete_uri(self, remote_path:str) -> None:
        response = self.session.delete(self.get_file_url(remote_path))
        if response.status_code != 204:
            raise RuntimeError(f"Failed to delete file from {self.get_file_url(remote_path)}: {response.text}")

    def list_files(self, remote_path:str) -> list[str]:
        aql_query = f'items.find({{"repo": "{self.repo}", "path": {{ "$match": "{remote_path}*"}} }})'
        response = self.session.post(f'{self.url}/api/search/aql', data=aql_query)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to list files from {self.url}: {response.text}")

        results = response.json()['results']

        files_list = []

        for item in results:
            path = item['path']
            if path == '.':
                path = ''
            files_list.append(f'{path}/{item["name"]}')

        return files_list
