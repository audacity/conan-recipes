[settings]
os = Macos
os.version=10.9
arch = x86_64
compiler = apple-clang
compiler.version = 14
compiler.libcxx = libc++
compiler.cppstd = 17
build_type = Release
[options]
catch2/*:no_std_unchaught_exceptions=True
