#include <portmidi.h>
#include <stdio.h>

int main() {
  int devices = Pm_CountDevices();
  printf("PortMidi devices: %d\n", devices);

  return 0;
}
