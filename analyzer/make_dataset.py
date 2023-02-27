import sys
from glob import glob

from features import features


def get_csp(test_csp_id):
    with open("testing_csp_list.txt", 'r') as f:
        for number, line in enumerate(f):
            if number == test_csp_id:
                return line.strip()
    return 0

def get_page(test_page_id):
    if test_page_id >= 100000000:
        test_page_id = test_page_id % 100000000
        with open("status_test_page_numbering.txt", 'r') as f:
            for number, line in enumerate(f):
                if number+1 == test_page_id:
                    return line.strip()
        return 0

    else:
        with open("test_page_numbering.txt", 'r') as f:
            for number, line in enumerate(f):
                if number == test_page_id:
                    return line.strip()
        return 0

def extract_csp_features(csp_features, features, csp_path):
    test_csp_id = int(csp_path.split("_")[-1].split(".csv")[0])
    test_csp = get_csp(test_csp_id)


    for directive_value in test_csp.split(";")[:-2]:
        directive_value = directive_value.strip()
        directive = directive_value.split(" ")[0]
        values = directive_value.split(" ")[1:]
        if values == []:
            col_name = "CSP-value:empty"
            csp_features[features['csp'].index(col_name)] = 1

        for value in values:
            if directive == "default-src":
                col_name = "CSP-directive:default-src"
            elif directive == "script-src":
                col_name = "CSP-directive:script-src"
            elif directive == "script-src-elem":
                col_name = "CSP-directive:script-src-elem"
            elif directive == "script-src-attr":
                col_name = "CSP-directive:script-src-attr"
            elif directive == "Default-src":
                col_name = "CSP-directive:Default-src"
            elif directive == "script=src":
                col_name = "CSP-directive:script=src"
            else:
                print (directive)
                print ("error!")
                sys.exit()

            csp_features[features['csp'].index(col_name)] = 1

            if "http://127.0.0.1:8000" in value:
                col_name = "CSP-value:http://127.0.0.1:8000"
            elif "가" in value:
                col_name = "CSP-value:nonascii"
            elif "Http://127.0.0.1:8080" in value:
                col_name = "CSP-value:http://127.0.0.1:8080"
            elif "http://127.0.0.1:8080" in value:
                col_name = "CSP-value:http://127.0.0.1:8080"
            elif "*" in value:
                col_name = "CSP-value:*"
            elif "data:" in value:
                col_name = "CSP-value:schemes"
            elif "self" in value:
                col_name = "CSP-value:self"
            elif "unsafe-inline" in value:
                col_name = "CSP-value:unsafe-inline"
            elif "Unsafe-inline" in value:
                col_name = "CSP-value:unsafe-inline"
            elif "unsafe-eval" in value:
                col_name = "CSP-value:unsafe-eval"
            elif "none" in value:
                col_name = "CSP-value:none"
            elif "nonce" in value:
                col_name = "CSP-value:nonce"
            elif "Nonce" in value:
                col_name = "CSP-value:capitalized-nonce"
            elif "strict" in value:
                col_name = "CSP-value:strict-dynamic"
            elif "HASH" in value:
                col_name = "CSP-value:hash"
            elif "unsafe-hashes" in value:
                col_name = "CSP-value:unsafe-hashes"
            else:
                continue
            csp_features[features['csp'].index(col_name)] = 1

def extract_page_features(page_features, features, test_page):
    page_content = get_page(test_page)
    page_elements = []
    for i in page_content.split("==page"):
        if "==" in i:
            page_elements.append(int(i.split("==")[0]))
    for i in page_elements:
        page_features[i] = 1

def extract_features(test_page, csv_path, executed):
    csp_features = []
    page_features = []
    browser_features = []
    status_features = []

    for i in range(len(features["csp"])):
        csp_features.append(0)
    for i in range(len(features["page"])):
        page_features.append(0)
    for i in range(len(features["browser"])):
        browser_features.append(0)
    status_features.append(features["status"])


    extract_csp_features(csp_features, features, csv_path)
    extract_page_features(page_features, features, test_page)
    if not executed == None:
      for bro in executed:
          browser_features[features['browser'].index(bro)] = 1

    if test_page > 100000000:
        status_features[0] = int (int(test_page) / 1000000)

    continas_19 = False
    if page_features[19] == 1:
        continas_19 = True
    return csp_features + page_features + browser_features + status_features, continas_19

def make_dataset(csv_path):

    chrome_empty_set = set()
    firefox_empty_set = set()
    safari_empty_set = set()

    chrome_empty_unique_set = set()
    firefox_empty_set = set()
    safari_empty_set = set()

    chrome_set = set()
    firefox_set = set()
    safari_set = set()

    with open("export/result_csp_0.csv", "r") as f:
        lines = f.readlines()

    for i in lines:
        split = i.strip().split(",")
        sign = split[0][1:-1].strip()
        sign = sign.replace('"', '')
        browser = split[1][1:-1].strip()
        if browser == "Chrome":
            chrome_empty_set.add(int(sign))
        elif browser == "Firefox":
            firefox_empty_set.add(int(sign))
        elif browser == "Safari":
            safari_empty_set.add(int(sign))

    union_empty_set = safari_empty_set.union(chrome_empty_set).union(firefox_empty_set)
    chrome_empty_false_set = union_empty_set - chrome_empty_set
    firefox_empty_false_set = union_empty_set - firefox_empty_set
    safari_empty_false_set = union_empty_set - safari_empty_set


    with open(csv_path, "r") as f:
        lines = f.readlines()

    for i in lines:
        split = i.strip().split(",")
        sign = split[0][1:-1].strip()
        sign = sign.replace('"', '')
        browser = split[1][1:-1].strip()
        if browser == "Chrome":
            chrome_set.add(int(sign))
        elif browser == "Firefox":
            firefox_set.add(int(sign))
        elif browser == "Safari":
            safari_set.add(int(sign))

    union_set = safari_set.union(chrome_set).union(firefox_set)
    inconsist_set = set()

    chrome_100 = []
    for i in chrome_empty_set:
        if i >=100000000 and i <= 100001000:
            chrome_100.append(i)


    for i in chrome_100  + list(union_empty_set - chrome_empty_false_set - firefox_empty_false_set - safari_empty_false_set):
        if not i in union_empty_set:
            continue
        executed = []
        not_executed = []
        if i in chrome_set:
            if not i in chrome_empty_false_set:
                executed.append("Chrome")
        else:
            if not i in chrome_empty_false_set:
                not_executed.append("Chrome")

        if i in firefox_set:
            if not i in firefox_empty_false_set:
                executed.append("Firefox")
        else:
            if i in chrome_100:
                not_executed.append("Firefox")
            elif not i in firefox_empty_false_set:
                not_executed.append("Firefox")

        if i in safari_set:
            if not i in safari_empty_false_set:
                executed.append("Safari")
        else:
            if i in chrome_100:
                not_executed.append("Safari")
            elif not i in safari_empty_false_set:
                not_executed.append("Safari")

        if executed == [] and not_executed == []:
            continue
        if len(executed) == 1 and not_executed == []:
            continue
        if executed == [] and len(not_executed) == 1:
            continue

        dataset = []
        if len(executed) >= 1 and len(not_executed) >= 1:
            # Inconsistency exist

            extracted_features, a = extract_features(i, csv_path, executed)
            if a:
                if ("Chrome" in executed) and ("Safari" in not_executed):
                    continue
                if ("Safari" in executed) and ("Chrome" in not_executed):
                    continue
            label = 1
            dataset = extracted_features + [label]

            print ("[*] test case #%s - executed: %s, non-executed: %s" % (i, executed, not_executed))
            test_csp_id = int(csv_path.split("_")[-1].split(".csv")[0])
            test_csp = get_csp(test_csp_id)
            print ("[*] testing CSP:", test_csp)
            print (dataset)
            print()
        else:
            # Inconsistency not existed
            extracted_features, a = extract_features(i, csv_path, None)
            label = 0
            dataset = extracted_features + [label]

            print ("[*] test case #%s - executed: %s, non-executed: %s" % (i, executed, not_executed))
            test_csp_id = int(csv_path.split("_")[-1].split(".csv")[0])
            test_csp = get_csp(test_csp_id)
            print ("[*] testing CSP:", test_csp)
            print (dataset)
            print ()

        converted_list = [str(element) for element in dataset]

        with open("features.txt", "a") as f:
            f.write(",".join(converted_list) + "\n")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Error: command")
        sys.exit()
    db_path = sys.argv[1]

    make_dataset(db_path)
