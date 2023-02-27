from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

import os

import argparse
import psutil

import subprocess
import sys
import json
import requests
import time
import signal

import hashlib
import base64
import urllib
from multiprocessing import Pool
from itertools import repeat

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

class Exception(Exception):
    pass

def alarm_handler(signum, frame):
    print("Time is up!")
    raise Exception()


def load_config(config_path):
    with open(config_path, "r") as f:
        config = json.load(f)
    return config

def initialize_browser(target_browser, config, p, headers):
    browser = None
    if target_browser == "Chrome":
        headers.update({
            'User-Agent': 'Chrome',
        })
        browser = p.chromium.launch()
    elif target_browser == "Edge":
        browser = p.chromium.launch()
        headers.update({
            'User-Agent': 'Edge',
        })
    elif target_browser == "Firefox":
        browser = p.firefox.launch()
        headers.update({
            'User-Agent': 'Firefox',
        })
    elif target_browser == "Safari":
        browser = p.webkit.launch()
        headers.update({
            'User-Agent': 'Safari',
        })

    return browser

def get_csp_list(csp_test_list):
    with open(csp_test_list) as f:
        return [s.strip() for s in f.readlines()]

def sha256_base64_url_encoding(data):
    sha256_encoded = hashlib.sha256(data.encode()).hexdigest()
    return urllib.parse.quote(base64.b64encode(bytes.fromhex(sha256_encoded)).decode())

def convert_hash(test_csp, test, csp_id, target_browser):
    converted_hashes = ""
    for i in test.split('} ')[1].split("HASH_SEPARATOR")[:-1]:
        if not i == '':
            csp_id_replaced = i.replace("$$$?", "?browser=" + str(target_browser)+ "&csp=" + str(csp_id) + "&")
            converted_hashes += "'sha256-" + sha256_base64_url_encoding(csp_id_replaced) + "' "
    converted_hashes = converted_hashes.strip()
    test_csp = test_csp.replace("'sha256-HASH'", converted_hashes)

    return test_csp

def get_csp_id(config, test_csp):
	with open(config['TOTAL_CSP_TEST_LIST'], 'r') as f:
		for number, line in enumerate(f):
			if test_csp == line.strip():
				return number
	return 0

def test_desktop(target_browser, target_csp_cnt, target_page_cnt, config, csp_list_path, elapsed_time):

    with sync_playwright() as p:

        headers = requests.utils.default_headers()
        browser = initialize_browser(target_browser, config, p, headers)
        csp_list = get_csp_list(csp_list_path)
        csp_cnt = 0
        page_cnt = 0
        context = browser.new_context()

        context.set_default_timeout(4000)
        page = context.new_page()


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

            with open(config["TEST_LIST"], mode="r") as f:
                for test in f:
                    if page_cnt < target_page_cnt:
                        page_cnt += 1
                        continue
                    target_page_cnt = 0 # reset page cnt for next CSP testing

                    ######### Check if the page is subject to CSP ######
                    test_split = test.split(" ")
                    page_name = test_split[0]

                    if "sha256-HASH"in test_csp:
                        test_csp_with_hash = convert_hash(test_csp, test, csp_id, target_browser)

                    ##################Broswer Testing###################
                    url = "{}{}?csp={}&browser={}".format(config["HOST"], page_name, test_csp_with_hash, target_browser)

                    print("[CSP {} Seq {}] Testing {}".format(csp_cnt, page_cnt, url))

                    try:
                        page.goto(url, wait_until="networkidle")
                    except:
                        print ("Except!")
                        page.close()
                        context.close()

                        browser = initialize_browser(target_browser, config, p, headers)

                        context = browser.new_context()

                        context.set_default_timeout(4000)
                        page = context.new_page()

                    if page_cnt % 100 == 0:
                        print ("Renew!!")
                        page.close()
                        context.close()

                        browser = initialize_browser(target_browser, config, p, headers)
                        context = browser.new_context()

                        context.set_default_timeout(4000)
                        page = context.new_page()
                    ####################################################

                    mid_time = time.time()
                    write_log(csp_id, "%s %lf ontesting" % (page_cnt, (mid_time - start_time + elapsed_time)), target_browser)
                    page_cnt += 1

                end_time = time.time()

                requests.get("{}?csp={}&browser={}".format(config["RESULT_API"], test_csp_with_hash, target_browser), headers=headers)
                write_log(csp_id, "finished: %lf" % (end_time - start_time + elapsed_time), target_browser)
                elapsed_time = 0
                context.close()
                break
    print ("==================End of CSP {} Testing===============\n\n".format(csp_cnt))
    target_csp_cnt += 1

    while True: # go to next csp testing.
    	log = read_log(target_csp_cnt, target_browser)
    	if log == 0:
    		target_page_cnt = 0
    		elapsed_time = 0
    		break
    	if (not ("finished" in log)) and (not ("ontesting" in log)):
    		write_log(target_csp_cnt, log + " ontesting", target_browser)
    		splitter = log.split(" ")
    		target_page_cnt = int(splitter[0])
    		elapsed_time = float(splitter[1])
    		break
    	target_csp_cnt += 1
    if not testing_end_check(csp_list_path, target_browser, target_csp_cnt):
    	test_desktop(target_browser, target_csp_cnt, target_page_cnt, config, csp_list_path, elapsed_time)



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


class PARAMETER:
	def __init__(self, target_browser, target_csp_cnt, target_page_cnt, config, csp_list_path, elapsed_time):
		self.target_browser = target_browser
		self.target_csp_cnt = target_csp_cnt
		self.target_page_cnt = target_page_cnt
		self.config = config
		self.csp_list_path = csp_list_path
		self.elapsed_time = elapsed_time

def run_test(parameter):
    test_desktop(parameter.target_browser, parameter.target_csp_cnt, parameter.target_page_cnt, parameter.config, parameter.csp_list_path, parameter.elapsed_time)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Tester for desktop browsers')
    ap.add_argument('-target_browser', '--target_browser', dest='target_browser', type=str, required=True)
    ap.add_argument('-start_csp', '--start_csp', dest='start_csp', type=int, required=True)
    ap.add_argument('-csp_file', '--csp_file', dest='csp_file', default='testing_csp_list.txt', type=str)
    ap.add_argument('-config_file', '--config_file', dest='config_file', default='conf.json', type=str)
    ap.add_argument('-num_core', '--num_core', dest='num_core', type=int, default=1, required=False)
    args = ap.parse_args()

    target_browser = args.target_browser
    target_csp_cnt = int(args.start_csp)

    config = load_config(args.config_file)

    init_logs() # remove "ontesting" label

    parameters = []

    current_csp_cnt = args.start_csp

    for id in range(args.num_core):

        while True:
        	log = read_log(current_csp_cnt, target_browser)
        	if log == 0:
        		break
        	if "finished" in log: # when the testing csp is already finished
        		current_csp_cnt += 1
        		continue
        	else:
        		break

        if testing_end_check(args.csp_file, args.target_browser, current_csp_cnt):
        	break

        if log == 0:  # file is not exist (corresponding csp is not tested yet)
        	target_page_cnt = 0
        	elapsed_time = 0
        else: # restore page_cnt and the elapsed time
        	splitter = log.split(" ")
        	target_page_cnt = int(splitter[0])
        	elapsed_time = float(splitter[1])

        parameters.append(PARAMETER(args.target_browser, current_csp_cnt, target_page_cnt, config, args.csp_file, elapsed_time))
        current_csp_cnt += 1

    pool = Pool(args.num_core)
    pool.map(run_test, parameters)
