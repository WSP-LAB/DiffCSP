CSP_FILE = "../testing_csp_list.txt"
OUTPUT_SQL = "install.sql"

SQL = '''
DROP DATABASE IF EXISTS cspuzz_result;
CREATE DATABASE cspuzz_result;
USE cspuzz_result;

DROP USER IF EXISTS 'cspuzz';

CREATE USER 'cspuzz'@'%' IDENTIFIED WITH mysql_native_password BY 'cspuzz';

FLUSH PRIVILEGES;

CREATE TABLE CSP_STATUS (csp_id INTEGER PRIMARY KEY, com_android_chrome BOOLEAN DEFAULT FALSE, com_UCMobile_intl BOOLEAN DEFAULT FALSE, org_mozilla_firefox BOOLEAN DEFAULT FALSE, com_opera_browser BOOLEAN DEFAULT FALSE, com_opera_mini_native BOOLEAN DEFAULT FALSE, com_uc_browser_en BOOLEAN DEFAULT FALSE, mobi_mgeek_TunnyBrowser BOOLEAN DEFAULT FALSE, com_yandex_browser BOOLEAN DEFAULT FALSE, com_explore_web_browser BOOLEAN DEFAULT FALSE, com_mx_browser BOOLEAN DEFAULT FALSE, org_adblockplus_browser BOOLEAN DEFAULT FALSE, com_apusapps_browser BOOLEAN DEFAULT FALSE);
CREATE TABLE CSP_LIST (csp_id INTEGER PRIMARY KEY, csp_directive TEXT);
{}

{}

GRANT ALL PRIVILEGES ON *.* TO 'cspuzz'@'%';

FLUSH PRIVILEGES;
'''

CSP_INSERT = "INSERT INTO CSP_LIST (csp_id, csp_directive) VALUES "
TABLE_CREATE = ""

# generate CSP list


with open(CSP_FILE, mode = "r") as f:
    cnt = 0
    res = []
    for l in f:
        res.append('({}, "{}")'.format(cnt, l.strip()))
        TABLE_CREATE += "CREATE TABLE result_csp_{} (test_sign INTEGER NOT NULL, browser CHAR(9) NOT NULL, CONSTRAINT PK_Test PRIMARY KEY (test_sign, browser));\n".format(cnt)
        cnt += 1
    CSP_INSERT += ','.join(res) + ";"

with open(OUTPUT_SQL, mode = "w") as f:
    f.write(SQL.format(CSP_INSERT, TABLE_CREATE))
