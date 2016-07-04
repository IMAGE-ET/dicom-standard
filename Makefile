PYTEST_BIN=python3 -m pytest

all: normalize_individual normalized_relationship

test: unittest endtoendtest

unittest: 
	$(PYTEST_BIN) -m 'not endtoend'

endtoendtest:
	$(PYTEST_BIN) -m 'endtoend'

normalized_relationship: dist/module_attr_relationship.json dist/ciod_module_relationship.json

normalize_individual: dist/ciods.json dist/modules.json dist/attributes.json

modules: dist/modules_raw.json

attributes: dist/complete_attrs.json

raw_attributes: dist/attributes_raw.json

dist/module_attr_relationship.json: tmp/complete_attrs.json
	python3 normalize_module_attr_relationship.py $< $@

dist/ciod_module_relationship.json: tmp/modules_raw.json
	python3 normalize_ciod_module_relationship.py $< $@

dist/ciods.json: tmp/modules_raw.json
	python3 normalize_ciods.py $< $@

dist/modules.json: tmp/complete_attrs.json
	python3 normalize_modules.py $< $@

dist/attributes.json: tmp/data_element_registry.json tmp/complete_attrs.json
	python3 normalize_attributes.py $^ $@

api/input/file_meta.json: api/input/ex_scan/IM-0001-0001.dcm
	python3 api/input/read_dicom_file.py $< $@

tmp/complete_attrs.json: tmp/attributes_raw.json tmp/data_element_registry.json
	python3 extend_attribute_properties.py $^ $@

tmp/data_element_registry.json: tmp/PS3.6-cleaned.html extract_data_element_registry.py
	python3 extract_data_element_registry.py $< $@

tmp/attributes_raw.json: tmp/PS3.3-cleaned.html modules_attributes.py
	python3 modules_attributes.py $< $@

tmp/modules_raw.json: tmp/PS3.3-cleaned.html ciod_modules.py
	python3 ciod_modules.py $< $@

tmp/PS3.3-cleaned.html: PS3.3.html
	cat $< | sed -e 's/&nbps;/ /g' > $@

tmp/PS3.6-cleaned.html: PS3.6.html
	cat $< | sed -e 's/&nbps;/ /g' -e 's/\\u200b//g' > $@

clean: 
	rm -f *.pyc tmp/* tests/*.pyc tests/*.pyc
