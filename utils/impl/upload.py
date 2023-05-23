import os
import subprocess
import json
from impl.utils import get_conan

recipes_remote_name = "conan-utils-audacity-recipes-conan2"
binaries_remote_name = "conan-utils-audacity-conan2"

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
        return

    subprocess.check_call([get_conan(), 'remote', 'add', name, url])

def remove_remote(name:str) -> None:
    try:
        subprocess.check_call([get_conan(), 'remote', 'remove', name])
    finally:
        pass

def upload_all(recipes_remote:str, binaries_remote:str) -> None:
    if not recipes_remote:
        recipes_remote = os.environ.get('CONAN_RECIPES_REMOTE', "https://artifactory.audacityteam.org/artifactory/api/conan/audacity-recipes-conan2")
    if not binaries_remote:
        binaries_remote = os.environ.get('CONAN_BINARIES_REMOTE', "https://artifactory.audacityteam.org/artifactory/api/conan/audacity-binaries-conan2")

    add_remote(recipes_remote_name, recipes_remote)
    add_remote(binaries_remote_name, binaries_remote)

    try:
        subprocess.check_call([get_conan(), 'upload', '--only-recipe', '--check', '--confirm', '-r', recipes_remote_name, '*'])
        subprocess.check_call([get_conan(), 'upload', '--check', '--confirm', '-r', binaries_remote_name, '*'])
    finally:
        remove_remote(recipes_remote_name)
        remove_remote(binaries_remote_name)

