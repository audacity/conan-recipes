import os
import re

import yaml
from cpt.packager import ConanMultiPackager

def build_package(package):
    ref = re.compile(r'/|@').split(package)

    root_package_dir = ref[0]

    package_config = yaml.load(open(os.path.join(root_package_dir, "config.yml"), "r"))

    versions = package_config["versions"]
    folder = versions[ref[1]]["folder"]

    builder = ConanMultiPackager(reference=package, conanfile=os.path.join(root_package_dir, folder, "conanfile.py"), visual_runtimes=["MD", "MDd"], msvc_versions=["193"],cppstds=["17"])
    builder.add_common_builds()
    builder.run_builds()

    print(builder)


if __name__ == "__main__":
    build_package("expat/2.3.0@audacity/stable")