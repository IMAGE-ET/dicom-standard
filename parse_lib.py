'''
Common functions for extracting information from the
DICOM standard HTML file.
'''

import json
import re
import sys
from functools import partial

from bs4 import BeautifulSoup
from bs4 import NavigableString

import parse_relations as pr

BASE_DICOM_URL = "http://dicom.nema.org/medical/dicom/current/output/html/"
SMALL_DICOM_URL_PREFIX = "http://dicom.nema.org/medical/dicom/current/output/chtml/part03/"

allowed_attributes = ["href", "src", "type", "data", "colspan", "rowspan"]

def parse_html_file(filepath):
    with open(filepath, 'r') as html_file:
        return BeautifulSoup(html_file, 'html.parser')


def write_pretty_json(data):
    json.dump(data, sys.stdout, sort_keys=False, indent=4, separators=(',', ':'))


def read_json_to_dict(filepath):
    with open(filepath, 'r') as json_file:
        json_string = json_file.read()
        json_dict = json.loads(json_string)
        return json_dict


def all_tdivs_in_chapter(standard, chapter_name):
    chapter_divs = standard.find_all('div', class_='chapter')
    for chapter in chapter_divs:
        if chapter.div.div.div.h1.a.get('id') == chapter_name:
            table_divs = chapter.find_all('div', class_='table')
            return table_divs


def create_slug(title):
    first_pass = re.sub(r'[\s/]+', '-', title.lower())
    return re.sub(r'[\(\),\']+', '', first_pass)


def find_tdiv_by_id(all_tables, table_id):
    table_with_id = [table for table in all_tables if pr.table_id(table) == table_id]
    return None if table_with_id == [] else table_with_id[0]


def clean_table_name(name):
    _, _, title = re.split('\u00a0', name)
    possible_table_suffixes = r'(IOD Modules)|(Module Attributes)|(Macro Attributes)|(Module Table)'
    clean_title, *_ = re.split(possible_table_suffixes, title)
    return clean_title.strip()


def clean_html(html):
    parsed_html = BeautifulSoup(html, 'html.parser')
    top_level_tag = get_top_level_tag(parsed_html)
    remove_attributes_from_html_tags(top_level_tag)
    remove_empty_children(top_level_tag)
    return resolve_relative_resource_urls(str(top_level_tag))


def get_top_level_tag(parsed_html):
    return next(parsed_html.descendants)


def remove_attributes_from_html_tags(top_level_tag):
    clean_tag_attributes(top_level_tag)
    for child in top_level_tag.descendants:
        clean_tag_attributes(child)


def clean_tag_attributes(tag):
    if not isinstance(tag, NavigableString):
        tag.attrs = {k: v for k, v in tag.attrs.items() if k in allowed_attributes}


def remove_empty_children(top_level_tag):
    empty_anchor_tags = filter((lambda a: a.text == ''), top_level_tag.find_all('a'))
    for anchor in empty_anchor_tags:
        anchor.decompose()


def resolve_relative_resource_urls(html_string):
    html = BeautifulSoup(html_string, 'html.parser')
    anchors = html.find_all('a', href=True)
    imgs = html.find_all("img", src=True)
    equations = html.find_all("object", data=True)
    list(map(resolve_anchor_href, anchors))
    list(map(partial(resolve_resource, 'src'), imgs))
    list(map(partial(resolve_resource, 'data'), equations))
    return str(html)


def resolve_anchor_href(anchor):
    if not has_protocol_prefix(anchor, 'href'):
        try:
            page, fragment_id = anchor['href'].split('#')
            resolved_page = 'part03.html' if page == '' else page
            anchor['href'] = resolved_page + '#' + fragment_id
        except ValueError:
            pass
        anchor['href'] = BASE_DICOM_URL + anchor['href']
        anchor['target'] = '_blank'


def has_protocol_prefix(resource, url_attribute):
    return re.match(r'(http)|(ftp)', resource[url_attribute])


def resolve_resource(url_attribute, resource):
    if not has_protocol_prefix(resource, url_attribute):
        resource[url_attribute] = BASE_DICOM_URL + resource[url_attribute]


def text_from_html_string(html_string):
    parsed_html = BeautifulSoup(html_string, 'html.parser')
    return parsed_html.text.strip()
