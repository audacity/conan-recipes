from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import get, export_conandata_patches, apply_conandata_patches, copy, collect_libs, replace_in_file
import os
import time

class PortMidiConan(ConanFile):
    name = "portmidi"
    description = "PortMidi is a computer library for real time input and output of MIDI data."
    topics = ("conan", "portmidi", "MIDI", "audio")
    url = "https://github.com/audacity/conan-recipes"
    homepage = "https://sourceforge.net/projects/portmedia/"
    license = "MIT"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False]
    }

    default_options = {
        "shared": False,
        "fPIC": True
    }

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC

    def configure(self):
        self.settings.rm_safe('compiler.libcxx')
        self.settings.rm_safe('compiler.cppstd')

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder=os.path.join('src', 'portmidi', 'trunk'))

    def source(self):
        get(
            self, **self.conan_data["sources"][self.version], strip_root=True,
            destination=os.path.realpath(os.path.join(self.source_folder, '..', '..')))

        apply_conandata_patches(self)

        replace_in_file(self, os.path.join(self.source_folder, 'CMakeLists.txt'), 'CMAKE_CACHEFILE_DIR', 'CMAKE_BINARY_DIR')

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["BUILD_SHARED"] = self.options.shared
        tc.variables["BUILD_STATIC"] = not self.options.shared
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)

        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.set_property("cmake_module_file_name", "PortMidi")
        self.cpp_info.set_property("cmake_module_target_name", "portmidi::portmidi")
        self.cpp_info.set_property("cmake_file_name", "PortMidi")
        self.cpp_info.set_property("cmake_target_name", "portmidi::portmidi")
        self.cpp_info.set_property("pkg_config_name", "portmidi")

        self.cpp_info.libs = collect_libs(self)

        if not self.options.shared:
            if self.settings.os == "Windows":
                self.cpp_info.system_libs.append('winmm')
            elif self.settings.os == "Macos":
                self.cpp_info.frameworks.extend(['CoreMIDI', 'CoreAudio', 'CoreFoundation', 'CoreServices'])
            else:
                self.cpp_info.system_libs.extend(['m', 'pthread', 'asound'])
