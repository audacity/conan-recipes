[settings]
os = Macos
os.version=10.13
arch = x86_64
compiler = apple-clang
compiler.version = 13
compiler.libcxx = libc++
compiler.cppstd = 17
build_type = Debug
[options]
*:shared=True
catch2/*:no_std_unchaught_exceptions=True
