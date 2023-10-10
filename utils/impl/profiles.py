import os
from impl.config import directories

def resolve_profile_path(path:str):
    if not os.path.isabs(path):
        path = os.path.join(directories.profiles_dir, path)

    if not os.path.exists(path):
        path += ".profile"
        if not os.path.exists(path):
            raise FileNotFoundError(f'Profile not found: {path}')

    return path


class ConanProfiles:
    def __init__(self, host_profile:str, build_profile:str):
        if not host_profile and not build_profile:
            raise ValueError('host_profile or build_profile must be specified')

        if host_profile:
            self.host_profile = host_profile
            if build_profile:
                self.build_profile = build_profile
            else:
                print('build_profile not specified, using host_profile as build_profile')
                self.build_profile = host_profile
        else:
            print('host_profile not specified, using build_profile as host_profile')
            self.host_profile = build_profile
            self.build_profile = build_profile

        self.host_profile = resolve_profile_path(self.host_profile)
        self.build_profile = resolve_profile_path(self.build_profile)

    def get_profile(self, build_context:bool):
        if build_context:
            return self.build_profile
        else:
            return self.host_profile

