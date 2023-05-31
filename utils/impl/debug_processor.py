from functools import cache
from impl.package_reference import PackageReference

__processors = {}

def register_debug_processor(processor_name:str, factory:callable):
    __processors[processor_name] = factory

def create_debug_processor(processor_name:str, skip_upload:bool):
    if processor_name not in __processors:
        raise ValueError(f'Unknown debug processor {processor_name}')

    return __processors[processor_name](skip_upload)

@cache
def load_processors():
    import os
    import importlib.util

    processors_path = os.path.join(os.path.dirname(__file__), 'debug_processors')
    for file in os.listdir(processors_path):
        if file.endswith('.py') and file != '__init__.py':
            module_name = file[:-3]
            spec = importlib.util.spec_from_file_location(module_name, os.path.join(processors_path, file))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

class DebugProcessor:
    def activate(self):
        return False

    def process(self, package_reference:PackageReference, source_dir: str, build_dir: str):
        pass

    def finalize(self):
        pass

    def discard(self):
        pass

