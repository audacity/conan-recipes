[settings]
os = Macos
os.version=10.9
arch = x86_64
compiler = apple-clang
compiler.version = 15
compiler.libcxx = libc++
compiler.cppstd = 17
build_type = RelWithDebInfo
[options]
*:shared=True
catch2/*:no_std_unchaught_exceptions=True
