# conan-recipes

This repository contains Conan recipes for Audacity dependencies that are not yet in Conal Center.

## wxWidgets

This recipe is based on https://github.com/bincrafters/community/tree/main/recipes/wxwidgets.

Few key differences:

* We use Conan components for better control over the libraries.
* wxUSE_ACCESSIBILITY is enabled on the supported platforms.
* We assume using GTK2 on all platforms, except Windows and macOS.
* We use a patched version of Audacity.

