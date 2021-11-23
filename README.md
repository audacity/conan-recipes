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

However, it uses autotools for *nix systems, as CMake build does not set the version correctly on macOS.

## libmp3lame

This recipe is based on https://github.com/conan-io/conan-center-index/tree/master/recipes/libmp3lame.

We add a patch for Cygwin builds to workaround https://sourceforge.net/p/lame/bugs/451/ 

## libtorch-binary

LibTorch library using the official binaries

## PortAudio

This recipe provides PortAudio v19.7.0

Patches:

### Windows

* `wasapi-loopback.patch` is based on Audacity patch by Leland Lucius.
* `pawinmme-export.patch` is based on https://github.com/PortAudio/portaudio/pull/503
* `winds-getguid.patch` adds `PaWinDS_GetDeviceGUID`, similar to `PaWasapi_GetIMMDevice`. This patch expects the `pawinmme-export.patch`.
  
### Linux

* `enable-oss.patch` reenable OSS host API when using CMake build system
  
## PortMidi

This recipe provides PortMidi built from r234 of PortMedia core

Patches:

* `build-system.patch` - adds CMake option to control the build precisely.
* `portmidi.h.patch` - correctly export `Pm_Synchronize` for the shared library builds.


## WavPack

This recipe provides WavPack 5.4.0
