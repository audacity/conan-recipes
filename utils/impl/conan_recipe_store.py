import os
import yaml

from impl.package_config_provider import package_config_provider
from impl.package_reference import PackageReference
from impl.config import directories
from impl.conan_recipe import ConanRecipe

class ConanRecipeStore:
    versions = None
    conan_references = {}
    package_config = None
    default_version = None

    def __init__(self, name: str):
        self.name = name
        self.path = os.path.join(directories.recipes_dir, name)

        if not os.path.exists(self.path):
            raise RuntimeError(f"Path `{self.path}` does not exist")

        config_path = os.path.join(self.path, 'config.yml')

        if not os.path.exists(config_path):
            raise RuntimeError(f"Config `{self.path}` does not exist")

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            self.versions = config['versions']

            for version in self.versions.keys():
                self.conan_references[version] = PackageReference(package_name=self.name, package_version=version)

        self.package_config = package_config_provider.get_package_config(self.name)

        if not self.package_config:
            raise RuntimeError(f"Package config for `{self.name}` not found")

        self.default_version = self.package_config['version']

    def get_recipe_folder(self, version:str) -> str:
        if not version in self.versions:
            raise RuntimeError(f"Version `{version}` not found. {', '.join(self.versions.keys())} available for {self.name}")

        recipe_folder = os.path.join(self.path, self.versions[version]['folder'])

        if not os.path.exists(recipe_folder):
            raise RuntimeError(f"Recipe folder `{recipe_folder}` does not exist")

        return recipe_folder

    def get_recipe(self, version:str) -> ConanRecipe:
        recipe_folder = self.get_recipe_folder(version)
        return ConanRecipe(recipe_folder, self.conan_references[version])

    def get_default_recipe(self) -> ConanRecipe:
        return self.get_recipe(self.default_version)

    def get_recipes(self):
        for version in self.versions.keys():
            yield self.get_recipe(version)

    def execute_command(self, command:str, all:bool):
        if all:
            for recipe in self.get_recipes():
                recipe.execute_command(command)
        else:
            self.get_default_recipe().execute_command(command)


def get_recipe_store(package_reference:PackageReference):
    return ConanRecipeStore(package_reference.name)

def get_recipe(package_reference:PackageReference):
    recipe_store = get_recipe_store(package_reference)
    return recipe_store.get_recipe(package_reference.version)

def get_recipe_stores(build_order:list[str], with_config_only:bool):
    visited = set()

    for package_name in build_order or []:
        visited.add(package_name)
        yield ConanRecipeStore(package_name)

    path = directories.recipes_dir

    for recipe in os.listdir(path):
        if recipe in visited:
            continue

        recipe_path = os.path.join(path, recipe)
        if not os.path.isdir(recipe_path):
            continue

        if not with_config_only:
            yield ConanRecipeStore(recipe)

        if package_config_provider.get_package_config(recipe):
            yield ConanRecipeStore(recipe)
