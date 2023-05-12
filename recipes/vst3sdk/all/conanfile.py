from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import get, export_conandata_patches, apply_conandata_patches, copy

import os

class Vst3SDKConan(ConanFile):
    name = "vst3sdk"
    license = "https://forums.steinberg.net/t/vst-3-sdk-license/201637"
    url = "https://github.com/audacity/conan-recipes"
    description = "VST3 SDK"
    topics = ("vst3")
    settings = "os", "compiler", "build_type", "arch"

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src/vst3sdk")

    def source(self):
        get(self,
            **self.conan_data["sources"][self.version],
            strip_root=True,
            destination=os.path.realpath(os.path.join(self.source_folder, '..')))

        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["SMTG_ADD_VST3_HOSTING_SAMPLES"] = False
        tc.cache_variables["SMTG_ADD_VST3_PLUGINS_SAMPLES"] = False
        tc.cache_variables["SMTG_ADD_VSTGUI"] = False
        tc.cache_variables["SMTG_CREATE_BUNDLE_FOR_WINDOWS"] = False
        tc.cache_variables["SMTG_MYPLUGINS_SRC_PATH"] = False
        tc.cache_variables["SMTG_RUN_VST_VALIDATOR"] = False
        tc.cache_variables["SMTG_CREATE_PLUGIN_LINK"] = False
        tc.generate()

    @property
    def safe_build_type(self):
        return "Debug" if self.settings.build_type == "Debug" else "Release"

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build(build_type=self.safe_build_type)

    def package(self):

        copy(self,
             "*.h",
             src=os.path.join(self.source_folder,  'vst3sdk', 'base'),
             dst=os.path.join(self.package_folder, 'include', 'base'),
             keep_path=True)

        copy(self,
             "*.h",
             src=os.path.join(self.source_folder,  'vst3sdk', 'pluginterfaces'),
             dst=os.path.join(self.package_folder, 'include', 'pluginterfaces'),
             keep_path=True)

        copy(self,
             "*.h",
             src=os.path.join(self.source_folder,  'vst3sdk', 'public.sdk', 'source'),
             dst=os.path.join(self.package_folder, 'include', 'public.sdk', 'source'),
             keep_path=True)

        copy(self,
             "*.h",
             src=os.path.join(self.source_folder,  'vst3sdk', 'public.sdk', 'source'),
             dst=os.path.join(self.package_folder, 'include', 'public.sdk', 'source'),
             keep_path=True)

        copy(self,
             "*.lib",
             src=self.build_folder,
             dst=os.path.join(self.package_folder, 'lib'),
             keep_path=True)

        copy(self,
             "*.dll",
             src=self.build_folder,
             dst=os.path.join(self.package_folder, 'bin'),
             keep_path=True)

        copy(self,
             "*.so",
             src=self.build_folder,
             dst=os.path.join(self.package_folder, 'lib'),
             keep_path=True)

        copy(self,
             "*.dylib",
             src=self.build_folder,
             dst=os.path.join(self.package_folder, 'lib'),
             keep_path=True)

        copy(self,
             "*.a",
             src=self.build_folder,
             dst=os.path.join(self.package_folder, 'lib'),
             keep_path=True)

    def package_info(self):
        self.cpp_info.components["base"].libs.append("base")
        self.cpp_info.components["pluginterfaces"].libs.append("pluginterfaces")
        self.cpp_info.components["sdk"].libs.append("sdk")
        self.cpp_info.components["sdk_common"].libs.append("sdk_common")
        self.cpp_info.components["sdk_hosting"].libs.append("sdk_hosting")
