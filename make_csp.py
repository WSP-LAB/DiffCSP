

import sys
import utils
import itertools
import copy
import re

def make_csp():
    gadgets = []
    val_gadgets = []
    key_list = ["default-src", "script-src", "script-src-attr", "script-src-elem"]
    white_list_urls = " http://127.0.0.1:8080"
    val_list = ["http://127.0.0.1:8000" + white_list_urls,
                "*",
                "data: mediastream: blob: filesystem: http: https:" + white_list_urls,
                "'self'" + white_list_urls,
                "'unsafe-inline'" + white_list_urls,
                "'unsafe-eval'" + white_list_urls,
                "'none'",
                "'nonce-123'" + white_list_urls,
                "'strict-dynamic'" + white_list_urls,
                "'sha256-HASH'" + white_list_urls,
                "'unsafe-hashes'" + white_list_urls]

    print ("empty") # Empty CSP

    for key in key_list:
        for value in val_list:
            gadgets.append(key + " " + value + ";")
            val_gadgets.append(key + " "+ value)

    for n in range(2,3):
        generator=itertools.combinations_with_replacement(val_gadgets, n)
        for i in generator:
            if not len(set(i)) == n:
                continue
            else:
                csp_dict = dict()
                for j in i:
                    key = j.split(" ")[0]
                    value = " ".join(j.split(" ")[1:])
                    if not key in csp_dict:
                        csp_dict[key] = [value]
                    else:
                        csp_dict[key].append(value)
                csp = ""
                for key in csp_dict:
                    csp += key
                    a = set()
                    for value in csp_dict[key]:
                        for i in value.split(" "):
                            a.add(i)
                    for k in list(a):
                      csp += " "
                      csp += k
                    csp += "; "
                gadgets.append(csp.strip())

    for s in gadgets:
        print (s + "connect-src http://127.0.0.1:8000;")


    # empty directive values
    print ("default-src;connect-src http://127.0.0.1:8000;")
    print ("script-src;connect-src http://127.0.0.1:8000;")
    print ("script-src-elem;connect-src http://127.0.0.1:8000;")
    print ("script-src-attr;connect-src http://127.0.0.1:8000;")

    # non-ascii URL
    print ("default-src http://127.0.0.1:8000 http://127.0.0.1가:8080 https://127.0.0.1:8081;connect-src http://127.0.0.1:8000;")
    print ("script-src http://127.0.0.1:8000 http://127.0.0.1가:8080 https://127.0.0.1:8081;connect-src http://127.0.0.1:8000;")
    print ("script-src-elem http://127.0.0.1:8000 http://127.0.0.1가:8080 https://127.0.0.1:8081;connect-src http://127.0.0.1:8000;")

    # typo - URL list
    print ("default-src http://127.0.0.1:8000 Http://127.0.0.1:8080 https://127.0.0.1:8081;connect-src http://127.0.0.1:8000;")
    print ("script-src http://127.0.0.1:8000 Http://127.0.0.1:8080 https://127.0.0.1:8081;connect-src http://127.0.0.1:8000;")
    print ("script-src-elem http://127.0.0.1:8000 Http://127.0.0.1:8080 https://127.0.0.1:8081;connect-src http://127.0.0.1:8000;")

    # typo - keyword
    print ("default-src 'Nonce-123' http://127.0.0.1:8080 https://127.0.0.1:8081;connect-src http://127.0.0.1:8000;")
    print ("script-src 'Nonce-123' http://127.0.0.1:8080 https://127.0.0.1:8081;connect-src http://127.0.0.1:8000;")
    print ("script-src-elem 'Nonce-123' http://127.0.0.1:8080 https://127.0.0.1:8081;connect-src http://127.0.0.1:8000;")

    # typo - directive
    print ("Default-src 'unsafe-inline' http://127.0.0.1:8080 https://127.0.0.1:8081;connect-src http://127.0.0.1:8000;")
    print ("script=src 'unsafe-inline' http://127.0.0.1:8080 https://127.0.0.1:8081;connect-src http://127.0.0.1:8000;")

if __name__ == '__main__':
    make_csp()
