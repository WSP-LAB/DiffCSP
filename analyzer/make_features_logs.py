import os, sys

for i in os.listdir("export"):
    if not "keep" in i:
        os.system("python3 make_dataset.py export/%s >> logs.txt" % i)
