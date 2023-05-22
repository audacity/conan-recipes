
from impl.package_config_provider import package_config_provider

class PackageReference:
    def __init__(self, package_name:str=None, package_version:str=None, package_user:str=None, package_channel:str=None, package_reference:str=None):
        if not package_reference:
            if not package_name:
                raise ValueError('package_name and package_version must be specified if package_reference is not specified')

            package_config = package_config_provider.get_package_config(package_name)
            if not package_version:
                if not package_config:
                    raise ValueError('package_version must be specified if package_reference is not specified and package_config is not found')
                package_version = package_config['version']

            if not package_user:
                package_user = package_config_provider.get_package_user(package_name, package_version)

            if not package_channel:
                package_channel = package_config_provider.get_package_channel(package_name, package_version)

            self.name = package_name
            self.version = package_version
            self.user = package_user
            self.channel = package_channel

            if self.user and self.channel:
                self.reference = f'{package_name}/{package_version}@{package_user}/{package_channel}'
            else:
                self.reference = f'{package_name}/{package_version}'
        else:
            self.reference = package_reference

            if '@' in package_reference:
                self.name, self.version = package_reference.split('@')[0].split('/')
                self.user, self.channel = package_reference.split('@')[1].split('/')
            else:
                self.name, self.version = package_reference.split('/')
                self.user = None
                self.channel = None

    def __str__(self):
        return self.reference

    def __repr__(self):
        return self.reference
