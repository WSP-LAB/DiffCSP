import os
import argparse
import subprocess
import time
import re

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
CMDLINE_TOOL_PATH = os.path.join(CURRENT_PATH, 'cmdline-tools/latest/bin')
PLATFORM_PATH = os.path.join(CURRENT_PATH, 'platform-tools')
EMULATOR_PATH = os.path.join(CURRENT_PATH, 'emulator')

def get_available_device():
	cmd_text = f'{PLATFORM_PATH}/adb devices'
	cmd_output = subprocess.run(cmd_text, shell=True, check=True, capture_output=True, text=True).stdout.strip()	
	device_id_list = []
	for line in cmd_output.split('\n'):
		if line.startswith('List of devices attached'):
			continue
		if 'offline' not in line:
			device_id = line.split('\t')[0]
			device_id_list.append(device_id)

	return device_id_list

def get_installed_apps(device):
	cmd = [f'{PLATFORM_PATH}/adb', '-s', device, 'shell', 'pm', 'list', 'packages', '-f']
	# app_lines = run_cmd(device, cmd).splitlines()
	app_lines = subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip().splitlines()	
	app_line_re = re.compile("package:(?P<apk_path>.+)=(?P<package>[^=]+)")
	package_to_path = {}
	for app_line in app_lines:
		m = app_line_re.match(app_line)
		if m:
			package_to_path[m.group('package')] = m.group('apk_path')
	
	return package_to_path

def install_app(apk, file_path, device):	
	if apk in get_installed_apps(device):
		print(f'{device} has installed {apk}!')
		return
	print(f'Installing {apk} on devices {device}')
	
	install_cmd = [f'{PLATFORM_PATH}/adb', '-s', device, 'install', '-r']
	install_cmd.append("-g")
	install_cmd.append(file_path)

	install_p = subprocess.Popen(install_cmd, stdout=subprocess.PIPE)
	count = 0
	while apk not in get_installed_apps(device):
		print("Please wait while installing the app...")
		count += 1
		time.sleep(5)		

	return True

def delete_emulators(num_devices):
	for i in range(1, num_devices + 1):
		cmd_text = f'{CMDLINE_TOOL_PATH}/avdmanager -v delete avd -n device_{i}'
		subprocess.run(cmd_text, shell=True)

def init_emulators_galaxy_nexus_android25(num_devices):		
	cmd_text = f'{CMDLINE_TOOL_PATH}/sdkmanager --install "platforms;android-25" "system-images;android-25;google_apis;x86"'
	subprocess.run(cmd_text, shell=True)
	print('Downloaded "platforms;android-25"!')

	print('Start creating emulators: Galaxy Nexus Android 25!')
	for i in range(1, num_devices + 1):
		cmd_text = f'{CMDLINE_TOOL_PATH}/avdmanager create avd -n device_{i} -k "system-images;android-25;google_apis;x86" --device "Galaxy Nexus" --force'
		subprocess.run(cmd_text, shell=True)

def init_emulators_pixel3_android30(num_devices):		
	cmd_text = f'{CMDLINE_TOOL_PATH}/sdkmanager --install "platforms;android-30" "system-images;android-30;google_apis;x86_64"'
	subprocess.run(cmd_text, shell=True)
	print('Downloaded "platforms;android-30"!')

	print('Start creating emulators: Pixel 3 Android 30!')
	for i in range(1, num_devices + 1):
		cmd_text = f'{CMDLINE_TOOL_PATH}/avdmanager create avd -n device_{i} -k "system-images;android-30;google_apis;x86_64" --device "pixel_3" --force'
		subprocess.run(cmd_text, shell=True)


def force_stop_all_emulators():
	kill_current_devices_cmd = "kill -9 $(ps aux | grep '[e]mulator/qemu/linux-x86_64/qemu-system-i386-headless @device_' | awk '{print $2}')"
	subprocess.run(kill_current_devices_cmd, shell=True)
	time.sleep(2)	

def start_emulators(num_devices):
	port = 5554
	for device in range(1,num_devices + 1):
		cmd_text = f'nohup {EMULATOR_PATH}/emulator @device_{device} -no-window -no-snapshot -memory 4096 -verbose -no-audio -camera-back none -camera-front none -no-boot-anim -screen no-touch -wipe-data -no-snapshot-load -no-snapshot-save -cores 2 -no-passive-gps -port {port}&'		
		subprocess.run(cmd_text, shell=True)				
		port += 2
		time.sleep(3)

	max_times = 0
	device_id_list = get_available_device()
	while len(device_id_list) < num_devices:
		if max_times >= 100:
			break
		device_id_list = get_available_device()
		print('Waiting for the devices to start!')
		time.sleep(2)
		max_times += 1


	device_id_list = get_available_device()
	print(f'Available devices: {device_id_list}')

	print('Switch to root and connect reverse proxy for adb command line.')
	for device_id in device_id_list:
		print(device_id)
		cmd_text = f'{PLATFORM_PATH}/adb -s {device_id} root'		
		subprocess.run(cmd_text, shell=True)
		# cmd_text = f'{PLATFORM_PATH}/adb -s {device_id} reverse tcp:8000 tcp:8000'		
		# subprocess.run(cmd_text, shell=True)
		# cmd_text = f'{PLATFORM_PATH}/adb -s {device_id} reverse tcp:8080 tcp:8080'		
		# subprocess.run(cmd_text, shell=True)
		# cmd_text = f'{PLATFORM_PATH}/adb -s {device_id} reverse tcp:8081 tcp:8081'		
		# subprocess.run(cmd_text, shell=True)
		# cmd_text = f'{PLATFORM_PATH}/adb -s {device_id} reverse tcp:8082 tcp:8082'		
		# subprocess.run(cmd_text, shell=True)
		# cmd_text = f'{PLATFORM_PATH}/adb -s {device_id} reverse tcp:8083 tcp:8083'		
		# subprocess.run(cmd_text, shell=True)


def install_apk(package_name, apk_file):
	device_id_list = get_available_device()
	for device_id in device_id_list:
		# cmd_text = f'{PLATFORM_PATH}/adb -s {device_id} install -g {apk_file}'		
		# subprocess.run(cmd_text, shell=True)	
		install_app(package_name, apk_file, device_id)	

def adb_root():
	device_id_list = get_available_device()
	for device_id in device_id_list:
		print(device_id)
		cmd_text = f'{PLATFORM_PATH}/adb -s {device_id} root'		
		subprocess.run(cmd_text, shell=True)

def main():
	ap = argparse.ArgumentParser(description='Cmd for setting up Android emulators')	
	ap.add_argument('-method', '--method', dest='method', type=str, required=True)
	ap.add_argument('-num_devices', '--num_devices', dest='num_devices', type=int)
	ap.add_argument('-package_name', '--package_name', dest='package_name', type=str)
	ap.add_argument('-apk_file', '--apk_file', dest='apk_file', type=str)
	ap.add_argument('-system_image', '--system_image', dest='system_image', type=str)

	args = ap.parse_args()		

	if args.method == 'init':
		if not args.system_image:
			print('Specifying the system image: android30, android25')
			return
		if args.system_image == 'android25':
			init_emulators_galaxy_nexus_android25(args.num_devices)
		if args.system_image == 'android30':
			init_emulators_pixel3_android30(args.num_devices)

	if args.method == 'delete':
		delete_emulators(args.num_devices)

	if args.method == 'start':
		start_emulators(args.num_devices)

	if args.method == 'stop':
		force_stop_all_emulators()

	if args.method == 'install':
		install_apk(args.package_name, args.apk_file)

	if args.method == 'root':
		adb_root()	

if __name__ == '__main__':
	main()
