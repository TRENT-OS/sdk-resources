# Platform Port for Hardkernel ODROID-C2

## Scope

This directory contains files related to the Hardkernel ODROID-C2 SBC.

## Files

The directory contains the following files:

- bl1.bin.hardkernel - first bootloader (proprietary)
- boot.scr           - Compiled U-Boot script from boot.script
- boot.script        - U-Boot script
- u-boot.gxbb        - signed image, containing all further bootloader components (BL2, BL30, BL301, BL31, U-Boot)

## Setup

The following steps describe a U-Boot based setup that allows to load a TRENTOS image via PXE boot.

### Prepare microSD card

At first, on a blank microSD card, two separate partitions (/boot and /rootfs) have to be created. The /boot partition shall then contain the U-Boot environment (boot.scr) that allows for setting up U-Boot with the PXE boot.

```bash
$ DEV=/dev/sda

# create two partitions (/boot and /rootfs) on the microSD card
# - partition /boot - FAT32 / 1GB
# - partition /rootfs - EXT4
# blank lines in the command correspond to pressing 'Enter' to accept default values from fdisk

$ sudo fdisk /dev/sda << EOF
n
p
1

+1G
t
b
n
p



t

83
w
EOF

# create file system for partition 1
$ sudo mkfs.vfat /dev/sda1 -n boot

# create file system for partition 2
$ sudo mkfs.ext4 /dev/sda2 -L rootfs
```

### Flash U-Boot script

After preparing the microSD card, the compiled U-Boot script has to be copied to the /boot partition.

```bash
# copy boot.scr to /boot partition
$ sudo cp boot.scr <path/to/boot/partition>
```

### Flash bootloader images

As a last step, both contents from u-boot.gxbb and bl1.bin.hardkernel have to be installed on the microSD card. Exemplarily, the card is to be seen as /dev/sda. This identifier must be adapted according to the individual setup. The actual flashing can then be done via the following commands:

```bash
$ DEV=/dev/sda

# Write the image to SD. Sector 0 holds the MBR, populate the first
# 442 byte with a boot loader. The space from byte 443 to the end is
# left untouched, because this contains the partition information
$ sudo dd if=bl1.bin.hardkernel of=$DEV conv=fsync bs=1 count=442
# The bootloader code continues from sector 1.
$ sudo dd if=bl1.bin.hardkernel of=$DEV conv=fsync bs=512 skip=1 seek=1

# put the at sector 97 (0xC200 = 97*512)
$ sudo dd if=u-boot.gxbb of=$DEV conv=fsync bs=512 seek=97
```

Beware: when defining the DEV variable above, make sure to select the actual microSD card (e.g. /dev/sda), and not a potential first partition (e.g. /dev/sda1)!