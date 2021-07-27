# conan-recipes

This repository contains Conan recipes for Audacity dependencies that are not yet in Conal Center.

## wxWidgets

This recipe is based on https://github.com/bincrafters/community/tree/main/recipes/wxwidgets.

Few key differences:

* We use Conan components for better control over the libraries.
* wxUSE_ACCESSIBILITY is enabled on the supported platforms.
* We assume using GTK2 on all platforms, except Windows and macOS.
* We use a patched version of Audacity.

## libmad and libid3tag

Audacity has a set of patches for these libraries. CMake build system is added, as the old
system does not play well on modern macOS. 

## libexpat

This recipe is based on https://github.com/conan-io/conan-center-index/tree/master/recipes/expat.

However, it uses autotools for *nix systems, as CMake build does not set the version correctly on macOS

## libmp3lame

This recipe is based onhttps://github.com/conan-io/conan-center-index/tree/master/recipes/libmp3lame.

We add a patch for Cygwin builds to workaround https://sourceforge.net/p/lame/bugs/451/ 

## libtorch-binary

LibTorch library using the official binaries
