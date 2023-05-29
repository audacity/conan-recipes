import subprocess
import json
from impl.utils import get_conan

def list_remotes() -> list[str]:
    remotes = subprocess.check_output([get_conan(), 'remote', 'list', '--format', 'json']).decode('utf-8')
    return json.loads(remotes)

def add_remote(name:str, url:str) -> None:
    remotes = list_remotes()
    for remote in remotes:
        if remote['name'] != name:
            continue
        if remote['url'] != url:
            subprocess.check_call([get_conan(), 'remote', 'update', '--url', name])
        return False

    subprocess.check_call([get_conan(), 'remote', 'add', name, url])
    return True

def remove_remote(name:str) -> None:
    try:
        subprocess.check_call([get_conan(), 'remote', 'remove', name])
    finally:
        pass
