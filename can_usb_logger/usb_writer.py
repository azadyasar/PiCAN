import os
from subprocess import check_output
from glob import glob
import time
import logging
import csv
logging.getLogger().setLevel(logging.INFO)


class USBWriter(object):
    def __init__(self):
        print("usbwriterinit")
        self.devices = self.get_mount_points()
        if len(self.devices) is not 0:
            logging.info(
                "USBWriter found USB Devices: {}".format(self.devices))
            self.target_usb = self.devices[0][1]
            self.target_file_path = os.path.join(
                self.target_usb, "test_" + str(time.time()) + ".csv")
            try:
                self.target_file = open(self.target_file_path, "w")
                self.csv_writer = csv.writer(self.target_file)
                self.is_targetfile_open = True
                logging.info(
                    "{} file will be used to store the log.".format(self.target_file_path))
            except IOError as ioErr:
                self.is_targetfile_open = False
                logging.warning("Couldn't open {} at the USB storage. Error: {}".format(
                    self.target_file_path, ioErr))
        else:
            logging.warning("USBWriter found no USB Devices.")
            self.is_targetfile_open = False
            self.target_file_path = "nofile"

    def get_usb_devices(self):
        sdb_devices = map(os.path.realpath, glob('/sys/block/sd*'))
        usb_devices = (
            dev for dev in sdb_devices if 'usb' in dev.split('/')[5])
        return dict((os.path.basename(dev), dev) for dev in usb_devices)

    def get_mount_points(self, devices=None):
        devices = devices or self.get_usb_devices()
        output = check_output(['mount']).decode().splitlines()
        #print("output: ", output)
        def is_usb(path): return any(dev in path for dev in devices)
        usb_info = (line for line in output if is_usb(line.split()[0]))
        #print("usb_info: ", usb_info)
        fullInfo = []
        for info in usb_info:
         #   print("info: ", info)
            mountURI = info.split()[0]
            usbURI = info.split()[2]
          #  print(info.split().__sizeof__())
            for x in range(3, info.split().__sizeof__()):
                if info.split()[x].__eq__("type"):
                    for m in range(3, x):
                        usbURI += " " + info.split()[m]
                    break
            fullInfo.append([mountURI, usbURI])
        return fullInfo
        # return [(info.split()[0], info.split()[2]) for info in usb_info]

    def writeLine(self, lines):
        if not self.is_targetfile_open:
            logging.warning("{} is not open to write.".format(
                self.target_file_path))
            return
        try:
            self.csv_writer.writerows(lines)
            # self.target_file.write(lines)
            # self.target_file.write('\n')
        except IOError as ioErr:
            logging.error("Error occured while writing [{}] to file [{}]. Details: {}".format(
                lines, self.target_file_path, ioErr))
            self.is_targetfile_open = False
        except Exception as ex:
            logging.error("Error occured while writing [{}] to file [{}]. Details: {}".format(
                lines, self.target_file_path, ex))
            self.is_targetfile_open = False
