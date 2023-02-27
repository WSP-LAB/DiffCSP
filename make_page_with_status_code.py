#!/usr/bin/python2

import sys
import utils
import re


signature = 1

def append_meta_data(page, template):
    a = page.split("<!--")[1].split("-->")[0]
    b = set()
    if not len(a) == 0:
        for i in a.split(","):
            if not i == "":
                b.add(i)


    if "location.href=" in template:
        b.add("location.href")
    if "location=" in template:
        b.add("location")
    if template.startswith("open("):
        b.add("open")
    if "window.open" in template:
        b.add("window.open")
    if "location.replace" in template:
        b.add("location.replace")
    if ".click()" in template:
        b.add("click")
#    if "document.write" in template:
#        b.add("document.write")


    c = "<!--"
    for i in b:
        c += i
        c += ","
    if c[-1] == ",":
        c = c[:-1]
    c += "-->"

    a = page.split("-->")[1]
    return c +  a

def append_meta_data_end(page, template):
    a = page.split("<!--")[1].split("-->")[0]
    b = set()
    if not len(a) == 0:
        for i in a.split(","):
            if not i == "":
                b.add(i)
    b.add("Script")

    c = "<!--"
    for i in b:
        c += i
        c += ","
    if c[-1] == ",":
        c = c[:-1]
    c += "-->"

    a = page.split("-->")[1]
    return c +  a


def config_traverse(page, config, depth, quote_list, slash_list, parent_template):
    global signature
    if "ID_VAR" in page:
        page = page.replace("ID_VAR", "GID_VARG")






    if "$$$" in page:
        page = append_meta_data_end(page, page)
        if "ID_VAR" in page:
            page = page.replace("ID_VAR", utils.random_char(5))
        for i in config['[HTML_RESOURCE]']+config['[JS_RESOURCE]']+config['[REPORT_API]']:
            if i in page:
                index=page.find(i)+len(i)
                print page[:index] + '?sign=%s' % signature + page[index:]
                signature += 1
        return 0

    if depth == 5:
        return -1

    for key in re.finditer(r"\[[^\[\]]*\]", page):
        idx_start_def = key.start(0)
        idx_end_def = key.end(0)
        key = page[idx_start_def: idx_end_def]
        for template in config[key]:
            page_def = page
            idx_start = idx_start_def
            idx_end = idx_end_def
            original_template = template
            if ('eval([JS])' in page) and 'document.close()' in template:
                template = template.replace(" document.close();", "")

            if ('eval([JS])' in page) and ' ' in template:
                continue

            if ("eval([JS])" in page) and (";" in template):
                continue

            new_quote_list = quote_list
            new_slash_list = slash_list



           # # Escaping is not needed for the following case

           # if ("='[JS]'" in parent_template) and ("localStorage" in template):
           #     page_split = page.split("[JS]")
           #     page_def = page_split[0][:page_split[0].rfind('=')+1] + \
           #             "[JS]" + \
           #             page_split[1][page_split[1].find('>'):]
           #     for key in re.finditer(r"\[[^\[\]]*\]", page_def):
           #         idx_start = key.start(0)
           #         idx_end = key.end(0)

  #          print "==============="
  #          print page
  #          print "==============="
  #          print

            # ID Assigning


            # quote escaping
            if "'" in template and (key == '[HTML]'):
                for quote in quote_list: # escaping for HTML
                    if '`' in quote or 'x60' in quote:
                        continue
                    template = template.replace("'", quote)
                    hhi = list(quote_list)
                    hhi.remove(quote)
                    new_quote_list = hhi
                    break
            elif "'" in template:
                #print quote_list
                template = template.replace("'", quote_list[0])
                new_quote_list = quote_list[1:]

            # slash escaping
            if (key == "[HTML]" and ('/' in template)) or (key == "[SVG]" and ('/' in template)):
                #print new_slash_list
 #               print page
 #               print
                template = template.replace("</", slash_list[0])
                if (not "iframe srcdoc" in template) and (not "data:" in template) and (not "<svg" in template) and (not "<template" in template):
                    new_slash_list = slash_list[1:]



            if key == "[HTML]" and ('nonce=123' in template):


                inserted_page = "".join((page_def[:idx_start], template, page_def[idx_end:]))
                #print inserted_page
                inserted_page = append_meta_data(inserted_page, template)
                config_traverse(inserted_page, config, depth + 1, new_quote_list, new_slash_list, original_template)

                template = template.replace(" nonce=123", "")
            inserted_page = "".join((page_def[:idx_start], template, page_def[idx_end:]))
            #print inserted_page

            inserted_page = append_meta_data(inserted_page, template)

            config_traverse(inserted_page, config, depth + 1, new_quote_list, new_slash_list, original_template)
            if key == "[HTML]":
                break

def make_page(config_path):
    config = utils.load_config(config_path)

    for template in config['[HTML]']:
        slash_list = ['</', '<\\/', '<\\\\/', '<\\\\\\\\/',  '<\\\\\\\\\\\\\\\\/', '<\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\/']
        quote_list = ['"', "'", '`', r"\x22", r"\\\x27", r"\\\\\x60",  "\\\\\\\\\x22"]
        # quote escaping
        if "'" in template:
            template = template.replace("'", quote_list[0])
            quote_list = quote_list[1:]

        if '/' in template:
            if (not "iframe srcdoc" in template) and (not "data:" in template) and (not "<svg" in template) and (not "<template" in template):
                    slash_list = slash_list[1:]
        template = "<!---->" + template
        template = append_meta_data(template, template)

        if 'nonce=123' in template:
            config_traverse(template, config, 1, quote_list, slash_list, template)

        template = template.replace(" nonce=123", "")
        config_traverse(template, config, 1, quote_list, slash_list, template)

    #for key in config:
    #    print key, config[key]


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print "Error: command"
        sys.exit()

    global signature

    config_path = sys.argv[1]
    signature = int(sys.argv[2]) * 1000000 + 1
    make_page(config_path)


