import argparse
import psutil

import subprocess
import sys
import json
import requests
import time
import signal

import os
import hashlib
import base64
import urllib
import tester_selenium

from multiprocessing import Pool
from itertools import repeat

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
PLATFORM_PATH = os.path.join(CURRENT_PATH, 'platform-tools')

LAUNCHER_MAPPING_DICT = {'com.android.chrome': 'com.google.android.apps.chrome.Main',
				'com.apusapps.browser': 'com.superapps.browser.main.SuperBrowserActivity',
				'com.xbrowser.play':'com.mmbox.xbrowser.BrowserActivity',
				'mark.via.gp':'mark.via.Shell',
				'com.duckduckgo.mobile.android':'com.duckduckgo.app.browser.BrowserActivity',
				'org.mozilla.firefox':'org.mozilla.fenix.IntentReceiverActivity',
				'com.opera.browser':'com.opera.android.BrowserActivity',
				'com.opera.mini.native':'com.opera.mini.android.Browser',
				'com.cloudmosa.puffinFree':'com.cloudmosa.app.FreeNormalActivity',
				'com.mx.browser':'com.mx.browser.MxSplashActivity',
				'com.brave.browser':'org.chromium.chrome.browser.ChromeTabbedActivity',
				'org.torproject.torbrowser':'org.mozilla.fenix.IntentReceiverActivity',
				'org.torproject.torbrowser_alpha':'org.mozilla.fenix.IntentReceiverActivity'}

MAX_TABS = 30

def testing_end_check(csp_file, package_name, target_csp_cnt):
	log_dir = 'logs'

	file = open(csp_file, "r")
	nonempty_lines = [line.strip("\n") for line in file if line != "\n"]
	line_count = len(nonempty_lines)

	if line_count < target_csp_cnt:
		return True

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


def clear_tabs_and_consent(package_name, device_id):	
	cmd_text = f'{PLATFORM_PATH}/adb -s {device_id} shell pm clear {package_name}'
	subprocess.run(cmd_text, shell=True)
	time.sleep(1)

	cmd_text = f'{PLATFORM_PATH}/adb -s {device_id} shell am start -n {package_name}/{LAUNCHER_MAPPING_DICT[package_name]} -a android.intent.action.VIEW -d "www.google.com"'
	subprocess.run(cmd_text, shell=True)
	time.sleep(1)

	cmd_text = f'{PLATFORM_PATH}/adb -s {device_id} shell am force-stop {package_name}'
	subprocess.run(cmd_text, shell=True)
	time.sleep(1)

	if os.path.isdir(f'browsers-cached/{package_name}'):
		for dir_name in os.listdir(f'browsers-cached/{package_name}'):
			cmd_text = f'{PLATFORM_PATH}/adb -s {device_id} push browsers-cached/{package_name}/{dir_name}/ /data/data/{package_name}'
			subprocess.run(cmd_text, shell=True)
	time.sleep(2)

	if package_name.startswith('org.torproject.torbrowser'):
		cmd_text = f'{PLATFORM_PATH}/adb -s {device_id} shell ls /data/data/{package_name}/files/mozilla/'
		cmd_output = subprocess.run(cmd_text, shell=True, check=True, capture_output=True, text=True).stdout.strip()
		profile_dir = ''
		for line in cmd_output.split('\n'):
			if line.endswith('.default'):
				profile_dir = line
				break
		local_pref_file = f'browsers-cached/{package_name}/prefs.js'
		pref_file = f'/data/data/{package_name}/files/mozilla/{profile_dir}/prefs.js'
		if not os.path.isfile(local_pref_file):			
			cmd_text = f'{PLATFORM_PATH}/adb -s {device_id} pull {pref_file} browsers-cached/{package_name}/'
			subprocess.run(cmd_text, shell=True)
			time.sleep(1)			
			with open(local_pref_file,'a+') as file:
				file.write('user_pref("network.proxy.no_proxies_on", "134.96.225.53");\n')
				file.write('user_pref("dom.disable_open_during_load", false);\n')
		cmd_text = f'{PLATFORM_PATH}/adb -s {device_id} push {local_pref_file} {pref_file}'
		subprocess.run(cmd_text, shell=True)		
		time.sleep(1)

def get_csp_id(config, test_csp):
	with open(config['TOTAL_CSP_TEST_LIST'], 'r') as f:
		for number, line in enumerate(f):
			if test_csp == line.strip():
				return number
	return 0

def write_log(current_csp, current_page, package_name):
	log_dir = 'logs'
	if not os.path.isdir(log_dir):
		os.makedirs(log_dir)
	log_file_path = os.path.join(log_dir, f'log_csp_{current_csp}_{package_name}.log')
	with open(log_file_path, 'w') as file:
		file.write(str(current_page))

def read_log(current_csp, package_name):
	log_file = f'logs/log_csp_{current_csp}_{package_name}.log'
	if not os.path.isfile(log_file):
		return 0
	with open(log_file, 'r') as file:
		page_cnt = file.read()
		return page_cnt

def init_logs():
	log_dir = 'logs'
	if not os.path.isdir(log_dir):
		return 0

	for log_file in os.listdir(log_dir):
		log_file_path = os.path.join(log_dir, log_file)

		with open(log_file_path, "r") as f:
			log = f.read()
		if "ontesting" in log:
			log = log.replace(" ontesting", "") # remove ontesting label
			with open(log_file_path, "w") as f:
				f.write(log)


def mobile_test(package_name, device_id, target_csp_cnt, target_page_cnt, config, csp_list_path, elapsed_time):
	csp_list = tester_selenium.get_csp_list(csp_list_path)
	csp_cnt = 0
	page_cnt = 0

	clear_tabs_and_consent(package_name, device_id)

	for test_csp in csp_list:
		test_csp_with_hash = test_csp
		if csp_cnt < target_csp_cnt:
			csp_cnt += 1
			continue

		start_time = time.time()

		csp_id = get_csp_id(config, test_csp)
		print(test_csp)
		print(csp_id)

		print(f'[*] Testing CSP {csp_cnt}: {test_csp}')
		num_current_tabs = 0

		with open(config['TEST_LIST'], 'r') as f:
			for test in f:
				if page_cnt < target_page_cnt:
					page_cnt += 1
					continue
				target_page_cnt = 0 # reset page cnt for next CSP testing

				######### Check if the page is subject to CSP ######
				test_split = test.split(' ')
				page_name = test_split[0]


				if 'sha256-HASH' in test_csp:
					test_csp_with_hash = tester_selenium.convert_hash(test_csp, test, csp_id, package_name)

				##################Broswer Testing###################
				url_encoded_csp = test_csp_with_hash.replace(" ", "%20")
				url_encoded_csp = url_encoded_csp.replace(";", "%3B")
				url_encoded_csp = url_encoded_csp.replace("'", "%27")

				url = f'{config["HOST"]}{page_name}?csp={url_encoded_csp}\&browser={package_name}'
				print(f'[CSP {csp_cnt} Seq {page_cnt}] Testing {url}')

				cmd_text = f'{PLATFORM_PATH}/adb -s {device_id} shell am start -n {package_name}/{LAUNCHER_MAPPING_DICT[package_name]} -a android.intent.action.VIEW -d "{url}"'
				subprocess.run(cmd_text, shell=True)
				if "sep" in url:
					time.sleep(1)
				else:
					time.sleep(3)

				num_current_tabs += 1

				if num_current_tabs >= MAX_TABS:
					clear_tabs_and_consent(package_name, device_id)
					num_current_tabs = 0

				####################################################

				mid_time = time.time()
				write_log(csp_cnt, "%s %lf ontesting" % (page_cnt, (mid_time - start_time + elapsed_time)), package_name)
				page_cnt += 1

			end_time = time.time()

			update_status_url = f'{config["RESULT_API"]}?csp={test_csp_with_hash}&browser={package_name.replace(".", "_").replace(".", "_")}'
			requests.get(update_status_url)
			write_log(csp_cnt, "finished: %lf" % (end_time - start_time + elapsed_time), package_name)
			elapsed_time = 0

			print (f'==================End of CSP {csp_cnt} Testing===============')
			target_csp_cnt += 1

			while True: # go to next csp testing.
				log = read_log(target_csp_cnt, package_name)
				if log == 0:
					target_page_cnt = 0
					elapsed_time = 0
					break
				if (not ("finished" in log)) and (not ("ontesting" in log)):
					write_log(target_csp_cnt, log + " ontesting", package_name)
					splitter = log.split(" ")
					target_page_cnt = int(splitter[0])
					elapsed_time = float(splitter[1])
					break
				target_csp_cnt += 1
			if not testing_end_check(csp_list_path, package_name, target_csp_cnt):
				mobile_test(package_name, device_id, target_csp_cnt, target_page_cnt, config, csp_list_path, elapsed_time)



class PARAMETER:
	def __init__(self, device_id, package_name, target_csp_cnt, target_page_cnt, config, csp_list_path, elapsed_time):
		self.device_id = device_id
		self.package_name = package_name
		self.target_csp_cnt = target_csp_cnt
		self.target_page_cnt = target_page_cnt
		self.config = config
		self.csp_list_path = csp_list_path
		self.elapsed_time = elapsed_time

def run_test(parameter):
	# print(parameter.device_id)
	# print(parameter.target_csp_cnt)
	# print(parameter.target_page_cnt)

	mobile_test(parameter.package_name, parameter.device_id, parameter.target_csp_cnt, parameter.target_page_cnt, parameter.config, parameter.csp_list_path, parameter.elapsed_time)

if __name__ == '__main__':
	ap = argparse.ArgumentParser(description='Tester for Android devices')
	ap.add_argument('-package_name', '--package_name', dest='package_name', type=str, required=True)
	ap.add_argument('-start_csp', '--start_csp', dest='start_csp', type=int, required=True)
	ap.add_argument('-csp_file', '--csp_file', dest='csp_file', default='testing_csp_list.txt', type=str)
	ap.add_argument('-config_file', '--config_file', dest='config_file', default='conf.json', type=str)
	ap.add_argument('-num_devices', '--num_devices', dest='num_devices', type=int, default=0, required=False)
	args = ap.parse_args()

	config = tester_selenium.load_config(args.config_file)
	device_ids = get_available_device()

	if args.num_devices != 0:
		device_ids = device_ids[0:args.num_devices]

	init_logs() # remove "ontesting" label

	parameters = []
	current_csp_cnt = args.start_csp



	for device_id in device_ids:
		while True:
			log = read_log(current_csp_cnt, args.package_name)
			if log == 0:
				break
			if "finished" in log: # when the testing csp is already finished
				current_csp_cnt += 1
				continue
			else:
				break

		if testing_end_check(args.csp_file, args.package_name, current_csp_cnt):
			break

		if log == 0:  # file is not exist (corresponding csp is not tested yet)
			target_page_cnt = 0
			elapsed_time = 0
		else: # restore page_cnt and the elapsed time
			splitter = log.split(" ")
			target_page_cnt = int(splitter[0])
			elapsed_time = float(splitter[1])

		parameters.append(PARAMETER(device_id, args.package_name, current_csp_cnt, target_page_cnt, config, args.csp_file, elapsed_time))
		current_csp_cnt += 1

	pool = Pool()
	pool.map(run_test, parameters)
