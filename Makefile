.SUFFIXES:

.PHONY:
	clean tests unittest endtoendtest updatestandard

PYTEST_BIN=python3 -m pytest


all: dist core_tables relationship_tables sitemaps dist/references.json

dist:
	mkdir dist

core_tables: dist/ciods.json dist/modules.json dist/attributes.json

relationship_tables: dist/ciod_to_modules.json dist/module_to_attributes.json


sitemaps: dist/ciod_to_modules.json
	python3 generate_sitemaps.py

# TODO: find a way around doing this
# module_to_attributes is made as a side effect when making references
dist/module_to_attributes.json: dist/references.json

dist/references.json: tmp/module_to_attributes_raw_description.json tmp/PS3.3-cleaned.html extract_references.py
	python3 extract_references.py tmp/references_raw.json dist/module_to_attributes.json $^
	cat tmp/references_raw.json | sed -e 's/\\u00a0/ /g' > $@

dist/ciod_to_modules.json: tmp/ciods_with_modules.json
	python3 normalize_ciod_module_relationship.py $< $@

tmp/module_to_attributes_raw_description.json: tmp/modules_with_attributes.json
	python3 normalize_module_attr_relationship.py $< $@


dist/ciods.json: tmp/ciods_with_modules.json
	python3 normalize_ciods.py $< $@

dist/modules.json: tmp/modules_with_attributes.json
	python3 normalize_modules.py $< $@

dist/attributes.json: tmp/PS3.6-cleaned.html extract_data_element_registry.py
	python3 extract_data_element_registry.py $< $@


tmp/ciods_with_modules.json: tmp/PS3.3-cleaned.html extract_ciods_with_modules.py
	python3 extract_ciods_with_modules.py $< $@

tmp/modules_with_attributes.json: tmp/modules_with_raw_attributes.json process_modules_with_attributes.py
	python3 process_modules_with_attributes.py $< $@

tmp/modules_with_raw_attributes.json: tmp/PS3.3-cleaned.html extract_modules_with_attributes.py
	python3 extract_modules_with_attributes.py $< $@


tmp/PS3.3-cleaned.html: PS3.3.html
	cat $< | sed -e 's/&nbps;/ /g' > $@

tmp/PS3.6-cleaned.html: PS3.6.html
	cat $< | sed -e 's/&nbps;/ /g' -e 's/​//g' > $@


tests: unittest endtoendtest

unittest:
	$(PYTEST_BIN) -m 'not endtoend'

endtoendtest:
	$(PYTEST_BIN) -m 'endtoend'


updatestandard:
	if [ ! -d old_standards ]; then mkdir old_standards; fi
	mv PS3.* old_standards/
	wget http://dicom.nema.org/medical/dicom/current/output/html/part03.html -O PS3.3.html
	wget http://dicom.nema.org/medical/dicom/current/output/html/part06.html -O PS3.6.html


clean:
	git clean -fqx dist tmp
	rm -rf dist
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
