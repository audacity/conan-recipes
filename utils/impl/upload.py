import os
import subprocess
from impl.utils import get_conan
from impl.remotes import add_remote, remove_remote

recipes_remote_name = "conan-utils-audacity-recipes-conan2"
binaries_remote_name = "conan-utils-audacity-binaries-conan2"


def upload_all(recipes_remote:str, binaries_remote:str) -> None:
    if not recipes_remote:
        recipes_remote = os.environ.get('CONAN_RECIPES_REMOTE', "https://artifactory.audacityteam.org/artifactory/api/conan/audacity-recipes-conan2")
    if not binaries_remote:
        binaries_remote = os.environ.get('CONAN_BINARIES_REMOTE', "https://artifactory.audacityteam.org/artifactory/api/conan/audacity-binaries-conan2")

    recipes_added = add_remote(recipes_remote_name, recipes_remote)
    binaries_added = add_remote(binaries_remote_name, binaries_remote)

    try:
        subprocess.check_call([get_conan(), 'upload', '--only-recipe', '--check', '--confirm', '-r', recipes_remote_name, '*'])
        subprocess.check_call([get_conan(), 'upload', '--check', '--confirm', '-r', binaries_remote_name, '*'])
    finally:
        if recipes_added:
            remove_remote(recipes_remote_name)
        if binaries_added:
            remove_remote(binaries_remote_name)

