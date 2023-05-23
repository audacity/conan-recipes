import os

from impl.package_reference import PackageReference
from impl.debug_processor import create_debug_processor, load_processors

__debug_processors = []

def enable_debug_processors(processors:list[str]):
    if not processors:
        return

    load_processors()

    for processor in processors:
        processor = create_debug_processor(processor)
        if not processor:
            print(f'Unknown debug processor {processor}')
            continue
        if processor.activate():
            __debug_processors.append(processor)

def finalize_debug_processors():
    for processor in __debug_processors:
        processor.finalize()

def handle_build_completed(package_reference:PackageReference, source_dir: str, build_dir: str):
    if len(__debug_processors) == 0:
        return

    if type(build_dir) is list:
        for dir in build_dir:
            if os.path.exists(dir):
                return handle_build_completed(package_reference, source_dir, dir)

        print(f'No build directory found for {package_reference}')
        return

    print(f'Processing debug info for {package_reference} ({source_dir}, {build_dir})')
    for processor in __debug_processors:
        processor.process(package_reference, source_dir, build_dir)
