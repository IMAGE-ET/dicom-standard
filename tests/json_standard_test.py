'''
Unit tests checking the json output from standard parsing.

These tests cover most of the functions in parse_lib.py. Functions
related to manipulating the tables (i.e. row or column span expansion)
are in the test_tables.py file.
'''

from bs4 import BeautifulSoup

import parse_lib as pl
import extract_ciods_with_modules as cm
import process_modules_with_attributes as ma
import normalize_ciods as nc
import normalize_modules as nm
import normalize_attributes as na
import normalize_ciod_module_relationship as ncm
import normalize_module_attr_relationship as nma
import tests.standard_snippets

def test_table_to_dict_conversion():
    '''
    Check that all JSON object values are correctly saved.
    '''
    table = [['1', '2', '3', '4'], ['5', '6', '7', '8'], ['9', '10', '11', '12']]
    column_titles = ['col1', 'col2', 'col3', 'col4']
    table_name = 'Table\u00a0TestSection\u00a0Some Element IOD Modules'
    table_id = "someID"
    table_dict = pl.table_to_dict(table, column_titles, table_name, table_id)
    assert table_dict['name'] == 'Some Element'
    for i in range(len(table_dict['data'])):
        for j in range(4):
            assert table_dict['data'][i][column_titles[j]] == table[i][j]

def test_add_descriptions_to_dict():
    json_dict = [{}, {}, {}]
    descriptions = ["First", "Second", "Third"]
    descriptions_dict = cm.add_ciod_description_fields(json_dict, descriptions)
    assert  descriptions_dict == [{"description": "First"},
                                  {"description": "Second"},
                                  {"description": "Third"}]

def test_get_text_or_href_from_html():
    '''
    Test text and href extraction. Note the dependence on the id <a></a> tag,
    which is present in every cell of the standard.
    '''
    cell = '<h3><a id="this is the id link"></a>This is a really cool <a href="link">link</a> to a website.</h3>'
    only_text = 'This is a really cool link to a website.'
    href_text = 'link'
    text = pl.text_or_href_from_cell(cell, 0, False)
    assert text == only_text
    link = pl.text_or_href_from_cell(cell, 2, True)
    assert link == href_text

def test_get_text_from_table():
    table = [['<h1>1</h1>', '<h1>2</h1>', '<h1>3</h1>', '<h1>4</h1>'],
             ['<h1>5</h1>', '<h1>6</h1>', '<h1>7</h1>', '<h1>8</h1>'],
             ['<h1>9</h1>', '<h1>10</h1>', '<h1>11</h1>', '<h1>12</h1>']]
    extract_links = False
    text_table = pl.extract_text_from_html(table, extract_links)
    expected_text_table = [['1', '2', '3', '4'], ['5', '6', '7', '8'], ['9', '10', '11', '12']]
    assert text_table == expected_text_table

def test_get_text_from_table_with_links():
    table = [['<h1>1</h1>', '<h1>2</h1>', '<h1><a id="some_id1"></a><a href="link1">3</a></h1>', '<h1>4</h1>'],
             ['<h1>5</h1>', '<h1>6</h1>', '<h1><a id="some_id2"></a><a href="link2">7</a></h1>', '<h1>8</h1>'],
             ['<h1>9</h1>', '<h1>10</h1>', '<h1><a id="some_id3"></a><a href="link3">11</a></h1>', '<h1>12</h1>']]
    extract_links = True
    text_table = pl.extract_text_from_html(table, extract_links)
    expected_text_table = [['1', '2', 'link1', '4'], ['5', '6', 'link2', '8'], ['9', '10', 'link3', '12']]
    assert text_table == expected_text_table

def test_extract_referenced_table_id():
    cell_html = '<td><p><span><a href="http://dicom.nema.org/medical/dicom/current/output/html/part03.html#sect_C.7.1.3"></a></span></p></td>'
    html = BeautifulSoup(cell_html, 'html.parser')
    cell = html.find('td')
    table_id = pl.extract_referenced_table_id(cell)
    assert table_id == "sect_C.7.1.3"

def test_find_table_div():
    divs = BeautifulSoup(tests.standard_snippets.divlist, 'html.parser').find_all('div', class_='table')
    table2 = pl.find_table_div(divs, 'tbl2')
    assert table2.a.get('id') == 'tbl2'

def test_table_to_list_no_macros():
    '''
    Check conversion of tables to lists with no macros present.
    Note: the long, unbroken string is unfortunately required for matching
    and cannot be indented for better readability.
    '''
    section = BeautifulSoup(tests.standard_snippets.cr_iod_section, 'html.parser')
    tdiv = section.find('div', class_='table')
    table = pl.table_to_list(tdiv)
    expected_html = '''<td align="left" colspan="1" rowspan="2">\n<p>\n<a id="para_5aa8b3f7-568e-412b-9b86-87014069f3a3" shape="rect"></a>Patient</p>\n</td>'''
    print(table[0][0])
    assert table[0][0] == expected_html

def test_table_to_list_with_macros():
    original_table = BeautifulSoup(tests.standard_snippets.macro_caller, 'html.parser')
    original_tdiv = original_table.find('div', class_='table')
    macro_list = BeautifulSoup(tests.standard_snippets.macro_callee, 'html.parser')
    macro_tables = macro_list.find_all('div', class_='table')
    table = pl.table_to_list(original_tdiv, macro_tables)
    print(table)
    assert table == [['<td>Useful Information</td>', None, None, None]]

def test_row_to_list():
    cell1 = '<td>Cell 1</td>'
    cell2 = '<td>Cell 2</td>'
    cell3 = '<td>Cell 3</td>'
    cell4 = '<td>Cell 4</td>'
    row_html = '<tr>' + cell1 + cell2 + cell3 + cell4 + '</tr>'
    row = BeautifulSoup(row_html, 'html.parser')
    cells = pl.convert_row_to_list(row)
    assert [cell1, cell2, cell3, cell4] == cells

def test_get_td_html():
    cell = '<td align="left" rowspan="2" colspan="1">This is <a href="content_link">some content</a> I want.</td>'
    content = pl.td_html_content(cell)
    assert content == 'This is <a href="content_link">some content</a> I want.'

def test_get_span_from_cell():
    inner_html = 'This is <a href="content_link">a cell</a> with spans to be expanded.'
    cell = '<td align="left" rowspan="2" colspan="1">' + inner_html + '</td>'
    span = pl.span_from_cell(cell)
    assert [2, 1, inner_html] == span

def test_extract_data_element_registry():
    from extract_data_element_registry import extract_table_data, properties_to_dict
    properties_table = BeautifulSoup(tests.standard_snippets.properties_snippet, 'html.parser')
    table = properties_table.find('div', class_='table')
    data = extract_table_data(table.div.table.tbody)
    json_data = properties_to_dict(data)
    expected_data = {
        "keyword": "Length ToEnd",
        "value_representation": "UL",
        "value_multiplicity": '1',
        "name": "Length to End",
        "retired": True
    }
    assert expected_data == json_data['(0008,0001)']

def test_clean_ciod_name():
    name = 'Table\u00a0A.2-1.\u00a0CR Image IOD Modules'
    final_name = 'CR Image'
    clean_name = pl.clean_table_name(name)
    assert clean_name == final_name

def test_clean_module_name():
    name = 'Table\u00a0C.26-4.\u00a0Substance Administration Log Module Attributes'
    final_name = 'Substance Administration Log'
    clean_name = pl.clean_table_name(name)
    assert clean_name == final_name

def test_clean_macro_name():
    name = 'Table\u00a08.8-1a.\u00a0Basic Code Sequence Macro Attributes'
    final_name = 'Basic Code Sequence'
    clean_name = pl.clean_table_name(name)
    assert clean_name == final_name

def test_get_ciod_slug_from_name():
    name = 'CR Image'
    expected_slug = 'cr-image'
    assert pl.create_slug(name) == expected_slug

def test_get_module_slug_from_name():
    name = 'Substance Administration Log'
    expected_slug = 'substance-administration-log'
    assert pl.create_slug(name) == expected_slug

def test_get_macro_slug_from_name():
    name = 'Basic Code Sequence'
    expected_slug = 'basic-code-sequence'
    assert pl.create_slug(name) == expected_slug

def test_add_parent_id_descending_order():
    test_modules = [
        {
            'data': [
                {
                    'name': 'Attribute 1',
                    'slug': '0001-0001',
                    'tag': '(0001,0001)',
                    'order': 0
                },
                {
                    'name': '>Attribute 2',
                    'slug': '0001-0002',
                    'tag': '(0001,0002)',
                    'order': 1
                },
                {
                    'name': '>>Attribute 3',
                    'slug': '0001-0003',
                    'tag': '(0001,0003)',
                    'order': 2
                }
            ]
        }
    ]
    ma.add_parent_ids_to_table(test_modules)
    assert test_modules[0]['data'][0]['parent_slug'] is None
    assert test_modules[0]['data'][1]['parent_slug'] == '0001-0001'
    assert test_modules[0]['data'][2]['parent_slug'] == '0001-0001:0001-0002'

def test_add_parent_id_different_levels():
    test_modules = [
        {
            'data': [
                {
                    'name': 'Attribute 1',
                    'slug': '0001-0001',
                    'tag': '(0001,0001)',
                    'order': 0
                },
                {
                    'name': '>Attribute 2',
                    'slug': '0001-0002',
                    'tag': '(0001,0002)',
                    'order': 1
                },
                {
                    'name': '>>Attribute 3',
                    'slug': '0001-0003',
                    'tag': '(0001,0003)',
                    'order': 2
                },
                {
                    'name': '>>>Attribute 4',
                    'slug': '0001-0004',
                    'tag': '(0001,0004)',
                    'order': 3
                },
                {
                    'name': '>>Attribute 5',
                    'slug': '0001-0005',
                    'tag': '(0001,0005)',
                    'order': 4
                },
                {
                    'name': '>Attribute 6',
                    'slug': '0001-0006',
                    'tag': '(0001,0006)',
                    'order': 5
                }
            ]
        }
    ]
    ma.add_parent_ids_to_table(test_modules)
    assert test_modules[0]['data'][0]['parent_slug'] is None
    assert test_modules[0]['data'][1]['parent_slug'] == '0001-0001'
    assert test_modules[0]['data'][2]['parent_slug'] == '0001-0001:0001-0002'
    assert test_modules[0]['data'][3]['parent_slug'] == '0001-0001:0001-0002:0001-0003' 
    assert test_modules[0]['data'][4]['parent_slug'] == '0001-0001:0001-0002'
    assert test_modules[0]['data'][5]['parent_slug'] == '0001-0001'

def test_add_parent_id_small_sequences():
    test_modules = [
        {
            'data': [
                {
                    'name': 'Attribute 1',
                    'slug': '0001-0001',
                    'tag': '(0001,0001)',
                    'order': 0
                },
                {
                    'name': '>Attribute 2',
                    'slug': '0001-0002',
                    'tag': '(0001,0002)',
                    'order': 1
                },
                {
                    'name': '>>Attribute 3',
                    'slug': '0001-0003',
                    'tag': '(0001,0003)',
                    'order': 2
                },
                {
                    'name': 'Attribute 4',
                    'slug': '0001-0004',
                    'tag': '(0001,0004)',
                    'order': 3
                },
                {
                    'name': '>Attribute 5',
                    'slug': '0001-0005',
                    'tag': '(0001,0005)',
                    'order': 4
                },
                {
                    'name': '>Attribute 6',
                    'slug': '0001-0006',
                    'tag': '(0001,0006)',
                    'order': 5
                }
            ]
        }
    ]
    ma.add_parent_ids_to_table(test_modules)
    assert test_modules[0]['data'][0]['parent_slug'] is None
    assert test_modules[0]['data'][1]['parent_slug'] == '0001-0001'
    assert test_modules[0]['data'][2]['parent_slug'] == '0001-0001:0001-0002'
    assert test_modules[0]['data'][3]['parent_slug'] is None
    assert test_modules[0]['data'][4]['parent_slug'] == '0001-0004'
    assert test_modules[0]['data'][5]['parent_slug'] == '0001-0004'

def test_find_non_adjacent_parent():
    attribute_list = [
        {
            'name': 'Attribute 1',
            'slug': '0001-0001',
            'parent_slug': None,
            'tag': '(0001,0001)',
            'order': 0
        },
        {
            'name': '>Attribute 2',
            'slug': '0001-0002',
            'parent_slug': '0001-0001',
            'tag': '(0001,0002)',
            'order': 1
        },
        {
            'name': '>>Attribute 3',
            'slug': '0001-0003',
            'parent_slug': '0001-0003',
            'tag': '(0001,0003)',
            'order': 2
        },
        {
            'name': '>Attribute 4',
            'slug': '0001-0004',
            'parent_slug': '0001-0004',
            'tag': '(0001,0004)',
            'order': 3
        }    
    ]
    previous_attribute = {
        'slug': '0001-0003',
        'sequence_indicator': '>>',
        'parent_slug': '0001-0002' 
    }
    parent_slug = ma.find_non_adjacent_parent('>', previous_attribute, attribute_list)
    assert parent_slug == '0001-0001'

def test_find_adjacent_parent():
    attribute_list = [
        {
            'name': 'Attribute 1',
            'slug': '0001-0001',
            'parent_slug': None,
            'tag': '(0001,0001)',
            'order': 0
        },
        {
            'name': '>Attribute 2',
            'slug': '0001-0002',
            'parent_slug': '0001-0001',
            'tag': '(0001,0002)',
            'order': 1
        }
    ]
    previous_attribute = {
        'slug': '0001-0001',
        'sequence_indicator': '',
        'parent_slug': None 
    }
    parent_slug = ma.record_parent_id_to_attribute('>', previous_attribute, attribute_list)
    assert parent_slug == '0001-0001'

def test_find_adjacent_parent_with_preceding_sibling_elements():
    attribute_list = [
        {
            'name': 'Attribute 1',
            'slug': '0001-0001',
            'parent_slug': None,
            'tag': '(0001,0001)',
            'order': 0
        },
        {
            'name': '>Attribute 2',
            'slug': '0001-0002',
            'parent_slug': '0001-0001',
            'tag': '(0001,0002)',
            'order': 1
        },
        {
            'name': '>Attribute 3',
            'slug': '0001-0003',
            'parent_slug': '0001-0001',
            'tag': '(0001,0003)',
            'order': 1
        }
    ]
    previous_attribute = {
        'slug': '0001-0002',
        'sequence_indicator': '>',
        'parent_slug': '0001-0001' 
    }
    parent_slug = ma.record_parent_id_to_attribute('>', previous_attribute, attribute_list)
    assert parent_slug == '0001-0001'

def test_normalize_ciods():
    test_ciod_list = [
        {
            'slug': 'ciod-1',
            'description': 'Some description of ciod 1.',
            'link_to_standard': 'http://somelink.com',
            'name': 'Ciod 1'
        }
    ]
    ciods = nc.ciod_table_from_raw_list(test_ciod_list)
    matching_entry = test_ciod_list[0]
    del matching_entry['slug']
    assert ciods['ciod-1'] == matching_entry

def test_normalize_modules():
    test_module_list = [
        {
            'slug': 'module-1',
            'link_to_standard': 'http://somelink.com',
            'name': 'Module 1'
        }
    ]
    modules = nm.module_table_from_raw_list(test_module_list)
    matching_entry = test_module_list[0]
    del matching_entry['slug']
    assert modules['module-1'] == matching_entry

def test_normalize_attributes():
    test_modules_with_attributes = [
        {
            'data': [
                {
                    'slug': '0001-0001',
                    'name': 'Attribute 1',
                    'parent_slug': None,
                    'type': None,
                    'description': None,
                    'tag': '(0001,0001)'
                }
            ]
        }
    ]
    attributes = na.extract_attributes(test_modules_with_attributes)
    matching_entry = {
        'name': 'Attribute 1',
        'parent_slug': None,
        'slug': '0001-0001',
        'type': None,
        'description': None,
        'tag': '(0001,0001)',
    }
    assert attributes['(0001,0001)'] == matching_entry

def test_normalize_ciod_module_relationship():
    ciod_module_list = [
        {
            "slug":"cr-image",
            "link_to_standard":"http://dicom.nema.org/medical/dicom/current/output/html/part03.html#table_A.2-1",
            "description":"\nThe Computed Radiography (CR) Image Information Object Definition specifies an image that has been created by a computed radiography imaging device.",
            "name":"CR Image",
            "data":[
                {
                    "information_entity":"Patient",
                    "conditional_statement":None,
                    "module":"Patient",
                    "link_to_standard":"http://dicom.nema.org/medical/dicom/current/output/html/part03.html#sect_C.7.1.1",
                    "usage":"M",
                },
            ]
        }
    ]
    relationship_table_list = ncm.ciod_module_relationship_table(ciod_module_list)
    expected_entry = {
        'ciod': 'cr-image',
        'module': 'patient',
        'usage': 'M',
        'conditional_statement': None,
        'order': 0,
        'information_entity': 'Patient'
    }
    assert relationship_table_list[0] == expected_entry

def normalize_module_attribute_relationship():
    module_attribute_list = [
        {
            "link_to_standard":"http://dicom.nema.org/medical/dicom/current/output/html/part03.html#table_C.2-1",
            "name":"Patient Relationship",
            "data":[
                {
                    "keyword":"ReferencedStudySequence",
                    "retired":False,
                    "value_representation":"SQ",
                    "tag":"(0008,1110)",
                    "parent_slug":None,
                    "description":"Uniquely identifies the Study SOP Instances associated with the Patient SOP Instance. One or more Items shall be included in this Sequence.See Section\u00a010.6.1.",
                    "slug":"0008-1110",
                    "value_multiplicity":"1",
                    "type":None,
                    "name":"Referenced Study Sequence",
                }
            ],
            "slug":"patient-relationship"
        }
    ]
    relationship_table_list = nma.module_attr_relationship_table(module_attribute_list)
    expected_entry = {
        'module': 'patient-relationship',
        'attribute': '0008-1110',
        'type': None,
        'order': 0
    }
    assert relationship_table_list[0] == expected_entry
