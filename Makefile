.PHONY: release install files test docs prepare publish

all:
	@echo "make release - prepares a release and publishes it"
	@echo "make dev - prepares a development environment"
	@echo "make install - install on local system"
	@echo "make todo - update todo files"
	@echo "make test - run tox"
	@echo "make docs - build docs"
	@echo "prepare - prepare module for release"
	@echo "make publish - upload to pypi"

release: test todo docs publish

dev:
	pip install -r dev-requirements.txt
	pip install -e $(shell pwd)

install:
	python setup.py install

todo:
	grep '# TODO' -rni * --exclude-dir=docs --exclude-dir=build --exclude=TODO.md | sed 's/: \+#/:    # /g;s/:#/:    # /g' | sed -e 's/^/- /' | grep -v Makefile > TODO.md

test:
	tox

docs:
	pip install -r docs/requirements.txt
	cd docs
	make html
	pandoc README.md -f markdown -t rst -s -o README.rst

prepare:
	python setup.py sdist

publish: prepare
	python setup.py upload

cleanup:
	rm -fr dist/ *.egg-info/ .tox/ .coverage
	find . -name "*.pyc" -exec rm -rf {} \;
