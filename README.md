# DiffCSP

DiffCSP is the first differential testing framework to find CSP enforcement
bugs involving JS execution.  The details of the testing strategy is in our
[paper](https://www.ndss-symposium.org/wp-content/uploads/2023/02/ndss2023_f200_paper.pdf),
"DiffCSP: Finding Browser Bugs in Content Security Policy Enforcement through
Differential Testing", which appeared in NDSS 2023. To see how to configure and
execute DiffCSP, see the followings.

## Setup
1. Install dependencies
```
$ pip install playwright
$ pip install pandas
$ pip install cikit-learn
```

2. Clone HiddenCPG
```
$ git clone https://github.com/WSP-LAB/DiffCSP.git
```
## Generation

#### Testing HTML

1. Execute `make_page.py` with the following command.

```
$ python2 make_page.py conf.json > test.html
```
Through this command, the pages to be tested are created line by line in the `test.html` file.

2. Execute preprocess.py with the following command.
```
$ python3 preprocess.py test.html 80
```
This command splits test.html into multiple files because the size of test.html is large and several pages (eg, redirection via window.open()) cannot coexist with other pages.

Executing this command produces two outputs:
1. `output` directory: the divided html files are saved in this  directory.
2. `test_list.txt` file: A file listing the names of the divided pages. This file will be used in browser testing (Step 2).

#### Testing CSP

```
$ python2 make_csp.py > testing_csp_list.txt
```
Through this command, you will get a list of CSPs to be tested (`testing_csp_list.txt`).

## Execution

#### Setting backend

1. Install the database
```
$ cd backend
$ python3 generate_sql.py
```
Through this command, you can get install.sql.
Please run this sql file into mysql.

Through this, a testing account of ID: `cspuzz`/ PW: `cspuzz` is created in
mysql, and a DB called `cspuzz_result` and its corresponding tables are created
for saving inconsistent results. Note that each table in `cspuzz_result` DB
represents each testing csp.

2. Executing the backend
```
$ cp -r output/* backend/src/test
$ cd backend/src
$ node app.js
```
Visit `http://127.0.0.1:8000/test/example.html`. If you can see "test" text in the browser, it means the backend is working well!

#### Run front-end automated browser testing

1. Move list of testing HTML file (`test_list.txt`) and CSP (`testing_csp_list.txt`) to the `tester` directory
```
$ cp test_list.txt tester
$ cp testing_csp_list.txt tester
$ cd tester
```

2. Execute destop browsers
```
$ python3 tester_playwright.py --target_browser [Chrome, Firefox, Safari] --start_csp 0
```

3. Execute mobile browsers

First, we need to the Android emulators. Check `mobile-setting` directory.

```
$ python3 tester_mobile.py --package_name [apk package name] --start_csp 0
```
Through this command, the specified browser visits each page for each CSP.


## Analysis

1. Export the testing results from DB
```
$ cd analyzer
$ ./export_db.sh
```
Through this command, testing results can be exported to `export` directory.

2. Make dataset

```
$ cd ..
$ cp test_list.txt analyzer
$ cp testing_csp_list.txt analyzer
$ cd analyzer
$ python3 make_features_logs.py
```
We can get the two output: `features.txt` and `logs.txt`.

3. Train and debug a decision tree
```
$ python3 decision_tree_train.py features.txt logs.txt
```

Then, we can get the debugging information (i.e., set of conditions) of each decision paths.
```
inconsist leaf!
250,895,,script-src-elem http://127.0.0.1:8080 'unsafe-inline' 'strict-dynamic';connect-src http://127.0.0.1:8000;
#895 - executed: ['Firefox', 'Safari'], non-executed: ['Chrome']
Rules used to predict sample 16239470:
decision id node 0 : (CSP-directive:default-src (= 0.0) <= 0.5)
decision id node 1 : (CSP-directive:script-src (= 0.0) <= 0.5)
decision id node 2 : (CSP-directive:script-src-elem (= 1.0) > 0.5)
decision id node 204 : (CSP-directive:script-src-attr (= 0.0) <= 0.5)
decision id node 205 : ([Write to static file] (= 0.0) <= 0.5)
decision id node 206 : (CSP-value:unsafe-inline (= 1.0) > 0.5)
decision id node 238 : (JS_EXECUTION_METHOD (= 1.0) <= 1.5)
decision id node 239 : (CSP-value:strict-dynamic (= 1.0) > 0.5)
decision id node 247 : ([Expending current HTML] (= 0.0) <= 0.5)
decision id node 248 : ([Eval of child frame] (= 1.0) > 0.5)
leaf node 250 reached, no decision here
```


# Citing DiffCSP
To cite our paper:
```
@INPROCEEDINGS{wi:ndss:2023,
    author = {Seongil Wi and Trung Tin Nguyen and Jihwan Kim and Ben Stock and Sooel Son},
    title = {{DiffCSP}: Finding Browser Bugs in Content Security Policy Enforcement through Differential Testing},
    booktitle = {Proceedings of the Network and Distributed System Security Symposium},
    year = 2023
}
```



