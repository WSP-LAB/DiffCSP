import os
import sys

with open("testing_csp_list.txt", "r") as f:
    a = f.readlines()

cnt = 1
fileno = 1
b = ''

num_file = int(sys.argv[1])


for line in a:
    name_su = (cnt % num_file)
    print name_su
    with open("testing_csp_%s.txt"%name_su, "a") as f:
        f.write(line)
    cnt += 1
