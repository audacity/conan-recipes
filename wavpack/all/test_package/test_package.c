#include <wavpack.h>
#include <stdio.h>

int main() {
  printf("WavPack version: %s\n", WavpackGetLibraryVersionString());

  return 0;
}
