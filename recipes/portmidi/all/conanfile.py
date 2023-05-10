from conans import ConanFile, tools, CMake
from conans.errors import ConanInvalidConfiguration
import os


class PortMidiConan(ConanFile):
    name = "portmidi"
    description = "PortMidi is a computer library for real time input and output of MIDI data."
    topics = ("conan", "portmidi", "MIDI", "audio")
    url = "https://github.com/audacity/conan-recipes"
    homepage = "https://sourceforge.net/projects/portmedia/"
    license = "MIT"
    settings = "os", "arch", "compiler", "build_type"
    generators = ["cmake", "cmake_find_package"]
    options = {
        "shared": [True, False],
        "fPIC": [True, False]
    }

    default_options = {
        "shared": False,
        "fPIC": True
    }

    exports_sources = ["CMakeLists.txt", "patches/*"]

    _cmake = None

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC

    def configure(self):
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = os.path.join("portmedia-code-" + self.version, "portmidi", "trunk")
        tools.rename(extracted_dir, self._source_subfolder)

        tools.patch(patch_file="patches/build-system.patch", base_path=self._source_subfolder)
        tools.patch(patch_file="patches/portmidi.h.patch", base_path=self._source_subfolder)

    def _configure_cmake(self):
        if self._cmake:
            return self._cmake

        cmake = CMake(self)

        cmake.definitions['BUILD_SHARED'] = self.options.shared
        cmake.definitions['BUILD_STATIC'] = not self.options.shared

        cmake.configure(build_folder=self._build_subfolder)

        self._cmake = cmake

        return self._cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy("LICENSE", dst="licenses", src=self._source_subfolder)

        cmake = self._configure_cmake()
        cmake.install()

    def package_info(self):
        self.cpp_info.name = "PortMidi"

        self.cpp_info.libs = self.collect_libs()

        if self.settings.os == "Windows" and not self.options.shared:
            self.cpp_info.system_libs.append('winmm')
        elif self.settings.os == "Macos":
            self.cpp_info.frameworks.extend(['CoreMIDI', 'CoreAudio', 'CoreFoundation', 'CoreServices'])
        else:
            self.cpp_info.system_libs.extend(['m', 'pthread', 'asound'])
