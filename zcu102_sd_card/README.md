# Platform Port for the Xilinx ZCU102

## Scope

This directory contains files related to the Xilinx ZCU102 platform.

## Files

These files represent the SD card setup that allows running a custom kernel
image on the Xilinx ZCU102 (TRENTOS-M image in our case). The required files
are:

- Device-tree blobs available after building the repository here:
<https://github.com/Xilinx/qemu-devicetrees>, both files are generated using the
commit `cd03ac` based on the version `xilinx-v2020.2`

  - `zynqmp-pmu.dtb` - Device tree blob used for the PMUFW boot component

  - `zcu102-arm.dtb` - Device tree blob used for the zcu102 PS (Cortex-A53 cluster)

- Pre-built binaries available in the configured PetaLinuxproject or in the BSP
here: <https://www.xilinx.com/support/download/index.html/content/xilinx/en/downloadNav/embedded-design-tools.html>.
The version `2020.2` of the zcu102 BSP was used for all 3 images:

  - `pmu_rom_qemu_sha3.elf` - PMU ROM image

  - `pmufw.elf` - PMU firmware

  - `bl31.elf` - Arm Trusted Firmware ELF file

- `u-boot.elf` - U-Boot ELF file, built from the configured PetaLinux project
created after successfully running the installer available here (installer
version `2020.2`):
  - <https://www.xilinx.com/support/download/index.html/content/xilinx/en/downloadNav/embedded-design-tools.html>

```bash
# Build PetaLinux
mkdir petalinux_install
cd petalinux_install
../petalinux-<VERSION>-final-installer.run
cd ..

# Create a dummy project to build configured u-boot
source petalinux_install/settings.sh
petalinux-create -t project -s xilinx-zcu102-v2020.2-final.bsp -n petalinux_proj
cd petalinux_proj

# After the gui settings window opens change the following 2 parameters:
#   bootcmd value = fatload mmc 0 0x8000000 os_image.elf;go 0x8000000
#   delay in seconds before automatically booting = 0
# <Save>
# <Exit>
petalinux-config -c u-boot

# Build the configured U-Boot
petalinux-build -c u-boot
```
