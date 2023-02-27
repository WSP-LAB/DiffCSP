import pymysql
import itertools
import sys
from delete_sign_list import delete_sign_list
import multiprocessing as mp

db = 0
cursor = 0
# Get a number of current CSP
def get_csp_count():
    global cursor
    cursor.execute("select count(*) from CSP_LIST");
    rows = cursor.fetchall()
    return rows[0][0]

# Get specific CSP by CSP ID
def get_csp_policy(csp_id):
    global cursor
    cursor.execute("select csp_directive from CSP_LIST where csp_id = {}".format(csp_id))
    rows = cursor.fetchall()
    return rows[0][0]

# Get a number of inconsistency by CSP ID
def get_inconsistent_count(csp_id):
    global cursor
    cursor.execute("select group_concat(browser) as browser, test_sign from result_csp_{} group by test_sign having count(*) < 3".format(csp_id))
    rows = cursor.fetchall()
    return rows # A list of (executable browser, test page signature)

# Add new CSP
def add_csp(cnt, csp_policy):
    global cursor
    try:
        cursor.execute("insert into CSP_LIST (csp_id, csp_directive) VALUES({}, \"{}\")".format(cnt, csp_policy))
        cursor.execute("create table result_csp_{} (test_sign int, browser char(9))".format(cnt))
    except:
        pass

# Modify CSP
def modify_csp(csp_id, new_policy, truncate = False):
    # Remove all previous test data when truncate is True
    global cursor
    cursor.execute("update CSP_LIST set csp_directive = \"{}\" where csp_id = {}".format(new_policy, csp_id))
    if truncate:
        cursor.execute("delete from result_csp_{}".format(csp_id))

def test_run(pool):
    csp_count = 991
    csp_ids = range(csp_count)
    c = list(itertools.product(csp_ids, delete_sign_list))
    pool.map(remove_page, c)

# Remove a page
def remove_page(c):
    global cursor
    csp_id = c[0]
    page_sign = c[1]
    print ("delete %s, %S" % (csp_id, page_sign ))
    cursor.execute("delete from result_csp_{} where test_sign = {}".format(csp_id, page_sign))

def get_csp_list(csp_test_list):
    with open(csp_test_list) as f:
        return [s.strip() for s in f.readlines()]

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print ("Error: command")
        sys.exit()

    user = sys.argv[1]
    password = sys.argv[2]
    db_name = sys.argv[3]

    db = pymysql.connect(host = "localhost", user = user, password=password, db = db_name, autocommit = True)
    cursor = db.cursor()


    # 1. Update CSP_LIST table
    csp_list = get_csp_list("testing_csp_list.txt")
    cnt = 0
    for csp in csp_list:
        if cnt == 1006:
            break

        if cnt >= 991:
            add_csp(cnt, csp)
        elif 'strict-dynamic' in csp:
            modify_csp(cnt, csp, True)
        else:
            modify_csp(cnt, csp, False)
        cnt += 1

    # 2. Remvoe test page
    pool = mp.Pool()
    test_run(pool)
