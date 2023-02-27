from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.firefox.options import Options
from msedge.selenium_tools import EdgeOptions
from msedge.selenium_tools import Edge
from selenium.webdriver.remote.command import Command
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

class Exception(Exception):
    pass

def alarm_handler(signum, frame):
    print("Time is up!")
    raise Exception()

def load_config(config_path):
    with open(config_path, "r") as f:
        config = json.load(f)
    return config

def initialize_driver(target_browser, config, headers):
    driver = None
    if target_browser == "Chrome":
        options = webdriver.ChromeOptions()
        options.add_argument('ignore-certificate-errors')
        options.add_argument('user-agent=Chrome')
        options.add_argument('headless')
        options.add_argument('disable-gpu')
        options.add_argument('disable-logging')
        headers.update({
            'User-Agent': 'Chrome',
        })
        driver = webdriver.Chrome(config["DRIVER_PATH"][target_browser], options = options, service_log_path='/dev/null')
    elif target_browser == "Edge":
        options = EdgeOptions()
        options.set_capability("acceptInsecureCerts", True)
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument("--user-agent=Edge");
        options.use_chromium = True
        options.add_argument("headless")
        options.add_argument("disable-gpu")
        options.set_capability("platform", "LINUX")
        caps = {}
        headers.update({
            'User-Agent': 'Edge',
        })
        driver = Edge(config["DRIVER_PATH"][target_browser], options = options, capabilities=caps)
    elif target_browser == "Firefox":
        options = Options()
        options.headless = True
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        profile = webdriver.FirefoxProfile()
        profile.accept_untrusted_certs = True
        profile.set_preference("general.useragent.override", "Firefox")
        profile.set_preference("security.csp.enable", True)
        profile.set_preference("webdriver.log.browser.ignore", True)
        profile.set_preference("webdriver.log.driver.ignore", True)
        profile.set_preference("webdriver.log.profiler.ignore", True)
        headers.update({
            'User-Agent': 'Firefox',
        })
        driver = webdriver.Firefox(options=options,executable_path=config["DRIVER_PATH"][target_browser], firefox_profile=profile, service_log_path=os.devnull)
    elif target_browser == "Safari":
        headers.update({
            'User-Agent': 'Safari',
        })
        driver = webdriver.Safari()

    return driver

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

def test(target_browser, target_csp_cnt, target_page_cnt, config, csp_list_path):
    headers = requests.utils.default_headers()
    driver = initialize_driver(target_browser, config, headers)
    csp_list = get_csp_list(csp_list_path)
    csp_cnt = 0
    page_cnt = 0


    for test_csp in csp_list:

        test_csp_with_hash = test_csp
        if csp_cnt < target_csp_cnt:
            csp_cnt += 1
            continue


        start_time = time.time()

        csp_id = 0
        print (test_csp)
        with open(config["TOTAL_CSP_TEST_LIST"], "r") as f:
            for number, line in enumerate(f):
                if test_csp == line.strip():
                    csp_id = number
                    break

        print("[*] Testing CSP {}: \"{}\"".format(csp_cnt, test_csp))
        with open(config["TEST_LIST"], mode="r") as f:
            for test in f:
                if page_cnt < target_page_cnt:
                    page_cnt += 1
                    continue
                target_page_cnt = 0 # reset page cnt for next CSP testing

                ######### Check if the page is subject to CSP ######
                test_split = test.split(" ")
                page_name = test_split[0]
                if test_csp != "empty":
                    csp_set_string = " ".join(test_split[1:]).strip()[1:-1]
                    test_flag = False
                    for directive in csp_set_string.split(", "):
                        if directive[1:-1] in test_csp:
                            test_flag = True
                    if test_flag == False:
                        continue


                if "sha256-HASH" in test_csp:
                    test_csp_with_hash = convert_hash(test_csp, test, csp_id, target_browser)

                ##################Broswer Testing###################

                url = "{}{}?csp={}&browser={}".format(config["HOST"], page_name, test_csp_with_hash, target_browser)

                print("[CSP {} Seq {}] Testing {}".format(csp_cnt, page_cnt, url))
                pid = driver.service.process.pid
                signal.signal(signal.SIGALRM, alarm_handler)
                if "sep" in url:
                    signal.setitimer(signal.ITIMER_REAL, 1.5)
                    driver.set_page_load_timeout(0.9)
                    driver.implicitly_wait(0.9)
                else:
                    signal.setitimer(signal.ITIMER_REAL, 3)
                    driver.set_page_load_timeout(3)
                    driver.implicitly_wait(3)

                try:
                    driver.get(url)

                    tabs = driver.window_handles #get list of open windows
                    first_tab = tabs[0]
                    for idx, val in enumerate(tabs):
                        if not val == first_tab:
                            driver.switch_to.window(tabs[idx])
                            driver.close()
                    driver.switch_to.window(first_tab)

                except TimeoutException as e:
                    print("Timeout occured in test {}".format(url))
                    #x = open("%s_timeout.txt"%target_browser, mode="a")
                    #x.write("{}\n".format(url))
                    #x.close()
                except:
                    print ("Except!")
                    signal.setitimer(signal.ITIMER_REAL,0)
                    #x = open("%s_exception.txt"%target_browser, mode="a")
                    #x.write("{}\n".format(url))
                    #x.close()

                    try:
                        parent_pid = pid   # my example
                        parent = psutil.Process(parent_pid)
                        for child in parent.children(recursive=True):  # or parent.children() for recursive=False
                            child.kill()
                        parent.kill()
                    except:
                        pass
                    driver = initialize_driver(target_browser, config, headers)
                    page_cnt -= 1
                finally:
                    signal.setitimer(signal.ITIMER_REAL,0)

                ####################################################
                page_cnt += 1
            requests.get("{}?csp={}&browser={}".format(config["RESULT_API"], test_csp_with_hash, target_browser), headers=headers)
            print ("==================End of CSP {} Testing===============".format(csp_cnt))
            end_time = time.time()
            print ("[*] execution time: %f\n\n" % (end_time - start_time))

            csp_cnt += 1
            page_cnt = 0

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("%s target_browser [target_csp_cnt] [target_page_cnt] [config_path]" \
                % sys.argv[0])
        sys.exit()
    target_browser = sys.argv[1]
    target_csp_cnt = 0
    target_page_cnt = 0
    csp_list_path = "csp_testing_list.txt"
    config_path = 'conf.json'

    if len(sys.argv) >= 3:
        target_csp_cnt = int(sys.argv[2])
    if len(sys.argv) >= 4:
        target_page_cnt = int(sys.argv[3])
    if len(sys.argv) >= 5:
        csp_list_path = sys.argv[4]

    config = load_config(config_path)
    test(target_browser, target_csp_cnt, target_page_cnt, config, csp_list_path)


