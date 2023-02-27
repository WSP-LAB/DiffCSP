import os, sys
import argparse
import psutil
import subprocess
import time
import signal

import tester_selenium

def byte_transform(bytes, to, bsize=1024):
    a = {'k' : 1, 'm': 2, 'g' : 3, 't' : 4, 'p' : 5, 'e' : 6 }
    r = float(bytes)
    for i in range(a[to]):
        r = r / bsize
    return round(r,2)

def get_emulator_ram_size():
    cmd_text = "ps xuaw |grep -e emulator -e COMMAND|grep -v grep |awk '{m=$5;sum += m;} END {print sum}'"
    cmd_output = subprocess.run(cmd_text, shell=True, check=True, capture_output=True, text=True).stdout.strip()
    ram_bytes = float(cmd_output) * 1000
    ram_gbytes = byte_transform(ram_bytes, 'g')
    return ram_gbytes


def stop_command():
    print ("Stop Emulator")
    os.system(r"kill -9 $(ps aux | grep '[t]ester_mobile.py' | awk '{print $2}')")
    os.system(r"kill -9 $(ps aux | grep '[g]eckodriver' | awk '{print $2}')")
    os.system(r"kill -9 $(ps aux | grep '[e]mulator' | awk '{print $2}')")
    time.sleep(2)

def start_command(num_devices, apk_file, package_name):
    print ("Start Emulator")
    cmd_text = "python3 cmd-emulators.py -method start -num_devices %d" % num_devices
    os.system(cmd_text)
    print ("Done!")
    time.sleep(8)
    print ("Install app")
    cmd_text = "python3 cmd-emulators.py -method install -apk_file %s -package_name %s" % (apk_file, package_name)

    while True:
        a = os.system(cmd_text)
        if a == 0:
            break
        time.sleep(2)
    print ("Done!")


def testing_end_check(csp_file, package_name):
    log_dir = 'logs'

    file = open(csp_file, "r")
    nonempty_lines = [line.strip("\n") for line in file if line != "\n"]
    line_count = len(nonempty_lines)

    for line in range(line_count):
        log_file_path = os.path.join(log_dir, f'log_csp_{line}_{package_name}.log')
        if os.path.exists(log_file_path):
            with open(log_file_path, "r") as f:
                log = f.read()
            if not "finished" in log:
                return False
        else:
            return False
    return True

def signal_handler(sig, frame):
    stop_command();
    sys.exit(0)

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Tester for Android devices with limited ram size')
    ap.add_argument('-apk_file', '--apk_file', dest='apk_file', type=str, required=True)
    ap.add_argument('-ram_size', '--ram_size', dest='ram_size', type=str, required=True)
    ap.add_argument('-package_name', '--package_name', dest='package_name', type=str, required=True)
    ap.add_argument('-start_csp', '--start_csp', dest='start_csp', type=int, required=True)
    ap.add_argument('-csp_file', '--csp_file', dest='csp_file', default='testing_csp_list.txt', type=str)
    ap.add_argument('-config_file', '--config_file', dest='config_file', default='conf.json', type=str)
    ap.add_argument('-num_devices', '--num_devices', dest='num_devices', type=int, default=0, required=False)
    args = ap.parse_args()

    apk_file = args.apk_file
    ram_size = args.ram_size
    package_name = args.package_name
    start_csp = args.start_csp
    csp_file = args.csp_file
    config_file = args.config_file
    num_devices = args.num_devices

    signal.signal(signal.SIGINT, signal_handler)


    while True:
        if testing_end_check(csp_file, package_name):
            print ("=========Testing ended for the package=========")
            break
        stop_command()
        start_command(num_devices, apk_file, package_name)
        cmd = "python3 %s/tester_mobile.py --package_name %s --start_csp %s --csp_file %s --config_file %s --num_devices %s" % (CURRENT_PATH, package_name, start_csp, csp_file, config_file, num_devices)
        p = subprocess.Popen(cmd, start_new_session=True, shell=True)


        while True:
            time.sleep(10)
            current_emulator_ram = get_emulator_ram_size()
            print ("[*] current emulator ram (%s), treshold (%s)" % (current_emulator_ram, ram_size))
            if current_emulator_ram > float(ram_size):
                  break
