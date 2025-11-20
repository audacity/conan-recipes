from pathlib import Path
from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps, cmake_layout
from conan.tools.files import get, export_conandata_patches, apply_conandata_patches, copy
import os

required_conan_version = ">=2.0.0"

class BreakpadConan(ConanFile):
    name = "breakpad"
    license = "https://chromium.googlesource.com/breakpad/breakpad/+/refs/heads/master/LICENSE"
    url = "https://github.com/audacity/conan-recipes"
    description = "Breakpad is a set of client and server components which implement a crash-reporting system."
    topics = ("breakpad", "crash-reporting")
    settings = "os", "compiler", "build_type", "arch"
    options = {"fPIC": [True, False]}
    default_options = {"fPIC": True}

    @property
    def needs_linux_syscall_support(self):
        return self.settings.os not in ("Windows", "Macos")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def layout(self):
        cmake_layout(self, src_folder="src")

    def export_sources(self):
        copy(self, "CMakeLists.txt", self.recipe_folder, self.export_sources_folder)
        export_conandata_patches(self)


    def generate(self):
        if self.needs_linux_syscall_support:
            copy(self,
                 "*.h",
                 src=self.dependencies.build["linux-syscall-support"].cpp_info.includedirs[0],
                 dst=os.path.join(self.source_folder, "src", "third_party", "lss"), keep_path=False)

        tc = CMakeToolchain(self)
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def source(self):
        # For some reason, with this recipe, the CMakeLists.txt file is not copied to the sources folder
        # in the local build mode.
        if not os.path.exists(os.path.join(self.source_folder, "CMakeLists.txt")):
            copy(self, "CMakeLists.txt", self.export_sources_folder, self.source_folder)

        get(self, **self.conan_data["sources"][self.version])
        apply_conandata_patches(self)

    def requirements(self):
        if self.settings.os != 'Windows':
            self.requires('libcurl/8.17.0@audacity/stable')

        if self.needs_linux_syscall_support:
            self.requires('linux-syscall-support/cci.20200813@audacity/stable', visible=False, build=True)

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self,
             "*.h",
             src=os.path.join(self.source_folder,  'src', 'google_breakpad'),
             dst=os.path.join(self.package_folder, 'include', 'google_breakpad'),
             keep_path=True)

        copy(self,
             "*.h",
             src=os.path.join(self.source_folder,  'src', 'processor'),
             dst=os.path.join(self.package_folder, 'include', 'processor'),
             keep_path=True)

        copy(self,
             "*.h",
             src=os.path.join(self.source_folder,  'src', 'client'),
             dst=os.path.join(self.package_folder, 'include', 'client'),
             keep_path=True)

        copy(self,
             "*.h",
             src=os.path.join(self.source_folder,  'src', 'common'),
             dst=os.path.join(self.package_folder, 'include', 'common'),
             keep_path=True)

        copy(self,
             "*.h",
             src=os.path.join(self.source_folder,  'src', 'third_party'),
             dst=os.path.join(self.package_folder, 'include', 'third_party'),
             keep_path=True)

        copy(self,
             "*.lib",
             src=self.build_folder,
             dst=os.path.join(self.package_folder, 'lib'),
             keep_path=False)

        copy(self,
             "*.dll",
             src=self.build_folder,
             dst=os.path.join(self.package_folder, 'bin'),
             keep_path=False)

        copy(self,
             "*.so",
             src=self.build_folder,
             dst=os.path.join(self.package_folder, 'lib'),
             keep_path=False)

        copy(self,
             "*.dylib",
             src=self.build_folder,
             dst=os.path.join(self.package_folder, 'lib'),
             keep_path=False)

        copy(self,
             "*.a",
             src=self.build_folder,
             dst=os.path.join(self.package_folder, 'lib'),
             keep_path=False)


    def package_info(self):
        self.cpp_info.components["client"].libs.append("breakpad_client")
        self.cpp_info.components["processor"].libs.append("breakpad_processor")
        self.cpp_info.components["sender"].libs.append("breakpad_sender")

        if self.settings.os == 'Linux' or self.settings.os == 'Macos':
            self.cpp_info.components['sender'].requires.append('libcurl::libcurl')
