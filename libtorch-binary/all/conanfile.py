from conans import ConanFile, tools, __version__ as conan_version
from conans.tools import Version

class Libtorch(ConanFile):
    name = "libtorch-binary"
    license = "https://raw.githubusercontent.com/pytorch/pytorch/master/LICENSE"
    url = "https://pytorch.org/"
    description = "Tensors and Dynamic neural networks in Python with strong GPU acceleration"
    settings = "os", "build_type"
    options = {"cuda": ["10.2", "11.1", "None"]}
    default_options = {"cuda": "None"}
    generators = "cmake"

    def build(self):
        _target_arch = str(self.options.cuda) if self.settings.os != "Macos" else "None"
        _target_os = str(self.settings.os)

        if self.settings.os == "Windows" and self.settings.build_type == "Debug":
            _target_os = _target_os + "-debug"
        
        tools.get(
            **self.conan_data["binaries"][self.version][_target_os][_target_arch])

    def package(self):
        self.copy("*", src="libtorch/", excludes=("*_python*", "*_test*"))

    def package_info(self):
        self.cpp_info.name = "Torch"
        self.cpp_info.libs = [lib for lib in self.collect_libs() if "_python" not in lib and "_test" not in lib]
        self.cpp_info.includedirs = ['include', 'include/torch/csrc/api/include']
        self.cpp_info.bindirs = ['bin']
        self.cpp_info.libdirs = ['lib']
