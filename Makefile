.PHONY: test full-test pep8 clean setup default

SRC=abilian/crm
PKG=$(SRC)

INSTANCE_FOLDER=$(shell 												\
	$(VIRTUAL_ENV)/bin/python											\
	 -c 'from flask import Flask; print Flask("myapp").instance_path')


default: test lint


#
# Environment
#
develop: setup-git update-env

setup-git:
	@echo "--> Configuring git and installing hooks"
	git config branch.autosetuprebase always
	cd .git/hooks && ln -sf ../../tools/hooks/* ./
	@echo ""

update-env:
	@echo "--> Installing/updating dependencies"
	pip install -U setuptools
	pip install -U -r requirements.txt
	pip install -e .
	@echo ""

#
# testing
#
test:
	py.test --tb=short $(PKG)

test-with-coverage:
	py.test --tb=short --durations 10 --cov $(PKG) --cov-config etc/coverage.rc \
	  --cov-report term-missing $(SRC)

test-long:
	RUN_SLOW_TESTS=True py.test -x $(SRC)

vagrant-tests:
	vagrant up
	vagrant ssh -c /vagrant/deploy/vagrant_test.sh
	# We could also do this:
	#vagrant ssh -c 'cp -a /vagrant src && cd src && tox'

#
# Linting / formatting
#
lint: lint-python lint-js

lint-python:
	@echo "--> Linting Python files"
	flake8 --config=setup.cfg abilian *.py

lint-js:
	@echo "--> Linting JavaScript files"
	@eslint abilian

format:
	isort -rc abilian
	yapf --style google -r -i abilian

clean:
	find . -name "*.pyc" | xargs rm -f
	find . -name .DS_Store | xargs rm -f
	find . -name __pycache__ | xargs rm -rf
	rm -rf instance/data instance/cache instance/tmp instance/webassets instance/whoosh
	rm -f migration.log
	rm -rf build dist
	rm -rf data tests/data tests/integration/data
	rm -rf tmp tests/tmp tests/integration/tmp
	rm -rf cache tests/cache tests/integration/cache
	rm -rf *.egg-info *.egg .coverage
	rm -rf whoosh tests/whoosh tests/integration/whoosh
	rm -rf doc/_build
	rm -rf static/gen static/.webassets-cache
	rm -rf htmlcov
	rm -rf junit-*.xml ghostdriver.log coverage.xml
	rm -rf tests.functional.test/

tidy: clean
	rm -rf instance
	rm -rf .tox

update-pot:
	python setup.py extract_messages update_catalog compile_catalog

release:
	rm -rf /tmp/abilian-crm-core
	git clone . /tmp/abilian-crm-core
	cd /tmp/abilian-crm-core ; python setup.py sdist
	cd /tmp/abilian-crm-core ; python setup.py sdist upload
