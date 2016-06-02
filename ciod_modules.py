'''
ciod_modules.py

Load the CIOD module tables from DICOM Standard PS3.3, Annex A.
Output the tables in JSON format, one entry per module.
'''
import json
import re
import sys

from bs4 import BeautifulSoup

import parse_lib as pl

def get_ciod_module_raw(standard_path, json_path):
    # standard = None
    # with open(standard_path, 'rb') as standard_file:
        # standard = pickle.load(standard_file)
    '''
    THIS IS INEFFICIENT. 
    1. Code above uses pickle to pass the parsable object between files. It doesn't work,
        the file is too big and pickle will either segfault or have a recursive timeout.
    2. Code blow simply recreates the beautifulsoup object, which is very time consuming.
    '''
    standard_file = open(standard_path, 'r')
    standard = BeautifulSoup(standard_file, 'html.parser')

    iod_table_pattern = re.compile(".*IOD Modules$")
    ciod_table_divs = pl.get_chapter_table_divs(standard, 'chapter_A')
    # Extract all the composite IOD tables 
    ciod_module_rough = open(json_path, 'w')
    for tdiv in ciod_table_divs:
        data = []
        table_name = tdiv.p.strong.get_text()
        if iod_table_pattern.match(table_name):
            table_body = tdiv.div.table.tbody
            urls = pl.extract_doc_links(table_body)
            table_fields = pl.separate_table_data(table_body, ['ies', 'modules', 'references', 'usage'], hanging_indent=True)
            ies = table_fields[0]
            modules = table_fields[1]
            references = table_fields[2]
            usage = table_fields[3]
            json_list = [table_name]
            for i in range (len(ies)):
                json_list.append({'IE Name': ies[i], 'Module': modules[i], 'Doc Reference': references[i], 'Usage': usage[i], 'URL':urls[i]})
            ciod_module_rough.write(json.dumps(json_list, sort_keys=True, indent=4, separators=(',',':')) + "\n")
    ciod_module_rough.close()

if __name__ == '__main__':
    try:
        get_ciod_module_raw(sys.argv[1], sys.argv[2])
    except IndexError:
        print("Not enough arguments specified. Please pass a path to the standard AND an output path for the JSON object.")
