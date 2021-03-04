# Platform Port for Raspberry Pi 4

## Scope

This directory contains files related to the Raspberry Pi 4 platform.

## Files

These files represent the SD card setup that allows running a custom kernel
image on the Raspberry Pi 4 (TRENTOS-M image in our case). The required files
are:

- bcm2711-rpi-4-b.dtb - Device tree blob that holds peripheral information,
available here:
  - <https://github.com/raspberrypi/firmware/tree/master/boot>

- start4.elf - Loads CPU bootloader and boots CPU, available here:
  - <https://github.com/raspberrypi/firmware/tree/master/boot>

- fixup4.dat - Linker files required for start.elf, available here:
  - <https://github.com/raspberrypi/firmware/tree/master/boot>

- u-boot.bin - A pre-built U-Boot image, can be built with in
<https://github.com/apritzel/u-boot/tree/rpi4-eth-v3>:

```bash
make CROSS_COMPILE=aarch64-linux-gnu- rpi_4_defconfig
make CROSS_COMPILE=aarch64-linux-gnu- -j8
```

- config.txt - Contains relevant configuration parameters for setting up the
RPi (e.g. enabling UART, JTAG, etc.)

- boot.scr - A user-defined image file that is read before the seL4 kernel
image, e.g. `os_image.elf`. Create from `boot.cmd` file with:

```bash
mkimage -A arm64 -T script -C none -n "Boot script" -d "boot.cmd" boot.scr
```
