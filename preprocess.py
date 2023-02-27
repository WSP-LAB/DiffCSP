import sys
import os
import utils
from enum import Enum
import hashlib
import base64

class VectorType(Enum):
    SCRIPT = 1
    LOCATION_HREF = 2
    LOCATION = 4
    WINDOW_OPEN = 8
    OPEN = 16
    REPLACE=32
    CLICK=64

META_MAP = {
    "Script": VectorType.SCRIPT,
    "location.href": VectorType.LOCATION_HREF,
    "location": VectorType.LOCATION,
    "window.open": VectorType.WINDOW_OPEN,
    #"document.write": VectorType.DOCUMENT_WRITE,
    "open": VectorType.OPEN,
    "location.replace": VectorType.REPLACE,
    "click": VectorType.REPLACE
}

HTML_STRUCT = "<html><head></head><body></body></html>\n"

def parseline(line):
    global META_MAP
    meta = 0
    data = line.split("-->")
    types = data[0].split("<!--")[1]
    for t in types.split(","):
        meta |= META_MAP[t].value
    return meta, data[1]

def in_separate(vector_type):
    return vector_type >= VectorType.LOCATION_HREF.value

def collect_csp(data):
    csp = set()
    csp.add('default-src')
    if 'script' in data:
        csp.add('script-src')
    if 'object' in data:
        csp.add('object-src')
    if 'frame' in data and not 'frames' in data:
        csp.add('frame-src')
        csp.add('child-src')
    if 'stylesheet' in data:
        csp.add('style-src')
    if 'img' in data:
        csp.add('img-src')
    if ('audio' in data) or ('video' in data) or ('mp3' in data):
        csp.add('media-src')
    if 'form' in data:
        csp.add('form-action')
    return csp

def collect_script_handler(data, handler, hashes, config):
    while True:
        if handler in data:
            sig = data.split(handler, 1)[0]
            data = data.split(handler, 1)[1]
            arr = config["[JS]"] + config["[HTML]"]
            min = 9999999
            for i in arr:
                if data.find(i[:3]) != -1:
                    if min > data.find(i[:3]):
                        min = data.find(i[:3])
            if min > 0:
                token = data[:min]
                data = data.split(token, 1)[1]
                data = data.rsplit(token, 1)[0]

                hashes.add(data)
        else:
            break
    return hashes

def sha256_base64_encoding(data):
    sha256_encoded = hashlib.sha256(data.encode()).hexdigest()
    return base64.b64encode(bytes.fromhex(sha256_encoded)).decode()

def collect_hashes(data, config):
    page = data
    hashes = set()
    while True:
        if "javascript:" in data:
            sig = data.split("javascript:", 1)[0]
            data = data.split("javascript:", 1)[1]
            arr = config["[JS]"] + config["[HTML]"]
            min = 9999999
            for i in arr:
                if data.find(i[:3]) != -1:
                    if min > data.find(i[:3]):
                        min = data.find(i[:3])
            if min == 0:
                for j in [r"\\\\\\\\\\\\\\\\'", r"\\\\\\\\'", r"\\\\'", r'\\\\`', r"\\'", r"\x27", r"\x22", '`', "'", '"']:
                    if j == (sig[(len(sig) - len(j)):]):
                        break
                data = data.rsplit(j, 1)[0]
                hashes.add(data)
            elif min > 0:
                token = data[:min]
                data = data.split(token, 1)[1]
                data = data.rsplit(token, 1)[0]
                data = token + data + token
                hashes.add(data)
        else:
            break

    data = page
    hashes = collect_script_handler(data, ' onanimationstart=', hashes, config)
    hashes = collect_script_handler(data, ' oncanplay=', hashes, config)
    hashes = collect_script_handler(data, ' ondurationchange=', hashes, config)
    hashes = collect_script_handler(data, 'onerror=', hashes, config)
    hashes = collect_script_handler(data, ' onload=', hashes, config)
    hashes = collect_script_handler(data, ' onloadeddata=', hashes, config)
    hashes = collect_script_handler(data, ' onloadedmetadata=', hashes, config)
    hashes = collect_script_handler(data, ' oninput=', hashes, config)
    hashes = collect_script_handler(data, ' oncopy=', hashes, config)
    hashes = collect_script_handler(data, ' onclick=', hashes, config)
    hashes = collect_script_handler(data, ' onchange=', hashes, config)
    hashes = collect_script_handler(data, ' ontoggle=', hashes, config)


    data = page

    while True:
        if '<script nonce=123>' in data:
            data = data.split("<script nonce=123>", 1)[1]
            data = data.rsplit("script>", 1)[0]
            data = data.rsplit("<", 1)[0]

            hashes.add(data)

        elif '<script>' in data:
            data = data.split("<script>", 1)[1]
            data = data.rsplit("script>", 1)[0]
            data = data.rsplit("<", 1)[0]
            hashes.add(data)

        else:
            break
    return hashes

def sep_status_write(status_code, TL, output_dir, sep_no, HTML_STRUCT, data, csp, hashes):
    w = open("{}/sep_{}_status_{}.html".format(output_dir, sep_no, status_code), mode="w")
    w.write(HTML_STRUCT)
    w.write(data)
    w.close()
    TL.write("sep_{}_status_{} {} ".format(sep_no, status_code, csp))
    for i in hashes:
        TL.write(i + "HASH_SEPARATOR")
    TL.write("\n")

def out_status_write(status_code, TL, output_dir, out_no, HTML_STRUCT, data, csp, hashes, pended_csp, pended_hash, pended):
    w = open("{}/out_{}_status_{}.html".format(output_dir, out_no, status_code), mode="w")
    w.write(HTML_STRUCT)
    w.write('\n'.join(pended))
    w.close()
    TL.write("out_{}_status_{} {} ".format(out_no, status_code, pended_csp))
    for i in pended_hash:
        TL.write(i + "HASH_SEPARATOR")
    TL.write("\n")


def preprocess(data_file, unit, output_dir):
    config = utils.load_config("conf.json")
    global HTML_STRUCT
    sep_no = 0
    out_no = 0
    pended = []
    pended_csp = set()
    pended_hash = set()

    TL = open("test_list.txt", mode="w")

    with open(data_file, mode="r") as f:
        for line in f:
            line_type, data = parseline(line.strip())
            #data = data.replace("143.248.249.43", "127.0.0.1").replace(":80", ":8000")
            csp = collect_csp(data)
            hashes = collect_hashes(data, config)
            if in_separate(line_type):
                if "status" in data_file:

                    status_code = data_file.split("_")[1].split(".")[0]
                    sep_status_write(status_code, TL, output_dir, sep_no, HTML_STRUCT, data, csp, hashes)
                    sep_no += 1
                else:
                    w = open("{}/sep_{}.html".format(output_dir, sep_no), mode="w")
                    w.write(HTML_STRUCT)
                    w.write(data)
                    w.close()
                    TL.write("sep_{} {} ".format(sep_no, csp))
                    for i in hashes:
                        TL.write(i + "HASH_SEPARATOR")
                    TL.write("\n")
                    sep_no += 1
            else:
                if (not ("document.write" in line)) and (not ("submit" in line)):
                    pended.append(data)
                    pended_csp |= csp
                    pended_hash |= hashes

                if len(pended) == unit:
                    if "status" in data_file:
                        status_code = data_file.split("_")[1].split(".")[0]
                        out_status_write(status_code, TL, output_dir, out_no, HTML_STRUCT, data, csp, hashes, pended_csp, pended_hash, pended)
                    else:
                        w = open("{}/out_{}.html".format(output_dir, out_no), mode="w")
                        w.write(HTML_STRUCT)
                        w.write('\n'.join(pended))
                        w.close()
                        TL.write("out_{} {} ".format(out_no, pended_csp))
                        for i in pended_hash:
                            TL.write(i + "HASH_SEPARATOR")
                        TL.write("\n")
                    pended = []
                    pended_csp = set()
                    pended_hash = set()
                    out_no += 1
    if len(pended) > 0:
        if "status" in data_file:
            status_code = data_file.split("_")[1].split(".")[0]
            w = open("{}/out_{}_status_{}.html".format(output_dir, out_no, status_code), mode="w")
            w.write('\n'.join(pended))
            w.close()
            TL.write("out_{}_status_{} {} ".format(out_no, status_code, pended_csp))
            for i in pended_hash:
                TL.write(i + "HASH_SEPARATOR")
            TL.write("\n")

            out_no += 1
        else:
            w = open("{}/out_{}.html".format(output_dir, out_no), mode="w")
            out_no += 1
            w.write('\n'.join(pended))
            w.close()
            TL.write("out_{} {} ".format(out_no, pended_csp))
            for i in pended_hash:
                TL.write(i + "HASH_SEPARATOR")
            TL.write("\n")

def main():
    if len(sys.argv) < 3:
        print("Usage: preprocess.py <data_file> <unit> [output_dir]")
        return
    data_file = sys.argv[1]
    unit = int(sys.argv[2])
    output_dir = sys.argv[3] if len(sys.argv) == 4 else "output"

    os.makedirs(output_dir, exist_ok = True)
    preprocess(data_file, unit, output_dir)

if __name__ == "__main__":
    main()
