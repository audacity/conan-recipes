import os
import sys

import yaml
from impl.config import directories

def get_build_order_path(build_order_name:str):
    if build_order_name:
        if os.path.isabs(build_order_name):
            return build_order_name
        return os.path.join(directories.config_dir, build_order_name)
    else:
        return os.path.join(directories.config_dir, 'build_order.yml')


def get_build_order(build_order_name:str):
    build_order_path = get_build_order_path(build_order_name)
    if not os.path.exists(build_order_path):
        raise Exception('Build order file does not exist: {}'.format(build_order_path))

    with open(build_order_path, 'r') as f:
        config = yaml.safe_load(f)['build_order']
        build_order = []

        for part in config:
            build_on = part['platforms']
            if build_on == '*' or sys.platform.lower() in build_on:
                build_order += part['packages']

    return build_order
