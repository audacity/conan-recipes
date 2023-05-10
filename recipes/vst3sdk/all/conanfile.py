from conans import ConanFile, CMake, tools
import os

class Vst3SDKConan(ConanFile):
    name = "vst3sdk"
    version = "3.7.3"
    license = "https://forums.steinberg.net/t/vst-3-sdk-license/201637"
    url = "https://github.com/audacity/conan-recipes"
    description = "VST3 SDK"
    topics = ("vst3")
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"
    exports_sources=[ 'CMakeLists.txt', "patches/*" ]

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])

        extracted_dir = os.path.join('VST_SDK', 'vst3sdk')
        tools.rename(extracted_dir, 'vst3sdk')

        tools.patch(base_path="vst3sdk", patch_file="patches/disable-validator.diff")
        tools.patch(base_path="vst3sdk", patch_file="patches/stdatomic-msvc.diff")

    def build(self):
        cmake = CMake(self)
        cmake.definitions["SMTG_ADD_VST3_HOSTING_SAMPLES"] = "OFF"
        cmake.definitions["SMTG_ADD_VST3_PLUGINS_SAMPLES"] = "OFF"
        cmake.definitions["SMTG_ADD_VSTGUI"] = "OFF"
        cmake.definitions["SMTG_CREATE_BUNDLE_FOR_WINDOWS"] = "OFF"
        cmake.definitions["SMTG_MYPLUGINS_SRC_PATH"] = ""
        cmake.definitions["SMTG_RUN_VST_VALIDATOR"] = "OFF"

        #In-source builds are not allowed
        cmake.configure(build_folder='build')
        cmake.build()

    def package(self):

        self.copy("*.h", dst="include/base", src="vst3sdk/base", keep_path=True)
        self.copy("*.h", dst="include/pluginterfaces", src="vst3sdk/pluginterfaces", keep_path=True)
        self.copy("*.h", dst="include/public.sdk/source", src="vst3sdk/public.sdk/source", keep_path=True)

        self.copy("*.lib", dst="lib", keep_path=False)
        self.copy("*.dll", dst="bin", keep_path=False)
        self.copy("*.so", dst="lib", keep_path=False)
        self.copy("*.dylib", dst="lib", keep_path=False)
        self.copy("*.a", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.components["base"].libs.append("base")
        self.cpp_info.components["pluginterfaces"].libs.append("pluginterfaces")
        self.cpp_info.components["sdk"].libs.append("sdk")
        self.cpp_info.components["sdk_common"].libs.append("sdk_common")
        self.cpp_info.components["sdk_hosting"].libs.append("sdk_hosting")
