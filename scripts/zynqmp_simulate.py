#
# Custom simulate script used for starting a TRENTOS-M system in QEMU for zynqmp
#
# Copyright (C) 2021, HENSOLDT Cyber GmbH
#

import sys
import time
import datetime
import os
import subprocess
import threading
import argparse

class Run_Context(object):
    #---------------------------------------------------------------------------
    def __init__(
        self,
        log_dir,
        hw_dir,
        resource_dir,
        system_image):

        self.log_dir      = log_dir
        self.hw_dir       = hw_dir
        self.resource_dir = resource_dir
        self.system_image = system_image

#-------------------------------------------------------------------------------
class qemu_generic:
    #---------------------------------------------------------------------------
    def __init__(self, binary, machine, cpu, memory, serial_ports, sd_card_image):
        self.binary = binary
        self.machine = machine
        self.cpu = cpu
        self.memory = memory
        self.kernel = None

        # By default this is off
        self.graphic = False

        # Enable for instruction tracing
        self.singlestep = False

        # SD card
        self.sd_card_image = sd_card_image

        # There can be multiple serial ports. Python guarantees the
        # order is preserved when adding elements to an array.
        self.serial_ports = serial_ports

        self.cmd_arr = []

        if self.machine:
            self.cmd_arr += ['-machine', self.machine]

        if self.cpu:
            self.cmd_arr += ['-cpu', self.cpu]

        if self.memory:
            self.cmd_arr += ['-m', 'size={}M'.format(self.memory)]

        if not self.graphic:
            self.cmd_arr += ['-nographic']

        if self.singlestep:
            self.cmd_arr += ['-singlestep']

        if self.kernel:
            self.cmd_arr += ['-kernel', self.kernel]

        # connect all serial ports
        for p in self.serial_ports:
            self.cmd_arr += ['-serial', p if p else 'null']

        if self.sd_card_image:
            self.cmd_arr += [
                '-drive',
                'file={},format=raw,id=mycard'.format(self.sd_card_image),
                '-device', 'sd-card,drive=mycard']

        self.cmd = [ self.binary ] + self.cmd_arr

    #---------------------------------------------------------------------------
    def add_params(self, *argv):
        for arg in argv:
            self.cmd.extend(arg)


#-------------------------------------------------------------------------------
class qemu_zcu102(qemu_generic):
    def __init__(self, cpu, memory, res_path, dev_path, serial_ports, sd_card_image):
        super().__init__('/opt/xilinx-qemu/bin/qemu-system-aarch64',
                            None, cpu, memory, serial_ports, sd_card_image)

        if res_path == None:
            raise Exception('ERROR: qemu_zcu102 requires the resource path')

        self.add_params([
            '-machine', 'arm-generic-fdt',
            '-dtb', os.path.join(res_path, 'zcu102-arm.dtb'),
            '-device', 'loader,file={},cpu-num=0'.format(os.path.join(res_path, 'bl31.elf')),
            '-device', 'loader,file={}'.format(os.path.join(res_path, 'u-boot.elf')),
            '-global', 'xlnx,zynqmp-boot.cpu-num=0',
            '-global', 'xlnx,zynqmp-boot.use-pmufw=true',
            '-machine-path', dev_path])


#-------------------------------------------------------------------------------
class qemu_microblaze(qemu_generic):
    def __init__(self, cpu, memory, res_path, dev_path):
        super().__init__('/opt/xilinx-qemu/bin/qemu-system-microblazeel',
                            None, cpu, memory, [], None)

        if res_path == None:
            raise Exception('ERROR: qemu_microblaze requires the resource path')

        self.add_params([
            '-machine', 'microblaze-fdt',
            '-dtb', os.path.join(res_path, 'zynqmp-pmu.dtb'),
            '-kernel', os.path.join(res_path, 'pmu_rom_qemu_sha3.elf'),
            '-device', 'loader,file={}'.format(os.path.join(res_path, 'pmufw.elf')),
            '-machine-path', dev_path])


#-------------------------------------------------------------------------------
def create_sd_img(sd_img_path, sd_img_size, sd_content_list = []):
    # Create SD image file
    #   - Create a binary file and truncate to the received size.
    with open(sd_img_path, 'wb') as sd_image_file:
        sd_image_file.truncate(sd_img_size)

    # Format SD to a FAT32 FS
    subprocess.check_call(['mkfs.fat', '-F 32', sd_img_path])

    # Copy items to SD image:
    #   - sd_content_list is a list of tuples: (HOST_OS_FILE_PATH, SD_FILE_PATH).
    #   - mcopy (part of the mtools package) copies the file from the linux host
    #     to the SD card image without having to mount the SD card first.
    for item in sd_content_list:
        subprocess.check_call([
            'mcopy',
            '-i',
            sd_img_path,
            item[0],
            os.path.join('::/', item[1])])


#===============================================================================
#===============================================================================

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('resource_path', help='Directory containing the zynqmp binaries used during the boot process')
    parser.add_argument('system_image', help='system image, e.g. os_image.elf')

    args = parser.parse_args()
    resource_path = args.resource_path
    system_image = args.system_image

    # In order to make sure the correct directory path is passed in, it is enough
    # to check for one of the binaries. We can assume the SDK contains all
    # the necessary files if the correct path is passed in.
    if not os.path.isfile(os.path.join(resource_path, 'pmufw.elf')):
        raise Exception('Invalid resource path! The directory should contain zynqmp resource binaries!')

    if not os.path.isfile(system_image):
        raise Exception('Invalid sytsem image path! The file does not exist!')


    #---------------------------------------------------------------------------
    out_dir = 'sim_out_{}'.format(datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
    log_dir = os.path.join(out_dir,'logs')
    hw_dir  = os.path.join(out_dir,'HW')

    os.makedirs(out_dir)
    os.makedirs(log_dir)
    os.makedirs(hw_dir)


    #---------------------------------------------------------------------------
    run_context = Run_Context(
            log_dir,
            hw_dir,
            resource_path,
            system_image)

    #---------------------------------------------------------------------------
    # Creating an SD image that contains the system binary which will
    # be booted by U-Boot
    sd_card_image_fqfn = os.path.join(run_context.hw_dir,'sdcard1.img')
    create_sd_img(sd_card_image_fqfn,
                    128*1024*1024, # 128 MB
                    [(run_context.system_image, 'os_image.elf')])


    #---------------------------------------------------------------------------
    # Initializing the MicroBlaze based PMU QEMU instance
    qemu_pmu = qemu_microblaze(
                None,
                None,
                os.path.join(run_context.resource_dir),
                run_context.hw_dir)

    # Initializing the ARM based zcu102 QEMU instance
    qemu_main = qemu_zcu102(
                    None,
                    4096,
                    os.path.join(run_context.resource_dir),
                    run_context.hw_dir,
                    [],
                    sd_card_image_fqfn)


    #---------------------------------------------------------------------------
    print(' ')
    print('QEMU PMU: {}'.format(' '.join(qemu_pmu.cmd)))
    print(' ')
    print('QEMU ZCU: {}'.format(' '.join(qemu_main.cmd)))
    print(' ')

    # Starting the MicroBlaze based PMU QEMU instance
    with open(os.path.join(log_dir,'qemu_pmu_out.txt'), 'w') as fout:
        with open(os.path.join(log_dir,'qemu_pmu_err.txt'), 'w') as ferr:
            process_pmu = subprocess.Popen(qemu_pmu.cmd, stdout=fout, stderr=ferr)

    # Starting the ARM based zcu102 QEMU instance
    process_zcu = subprocess.Popen(qemu_main.cmd)
    return_code = process_zcu.wait()


#===============================================================================
#===============================================================================

if __name__ == '__main__':
    # execute only if run as a script
    main()
