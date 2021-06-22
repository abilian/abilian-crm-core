.PHONY: test full-test flake8 clean setup default

PKG=abilian

INSTANCE_FOLDER=$(shell 												\
	$(VIRTUAL_ENV)/bin/python											\
	 -c 'from flask import Flask; print Flask("myapp").instance_path')


all: test lint

#
# Environment
#
develop: setup-git update-env

setup-git:
	@echo "--> Configuring git"
	git config branch.autosetuprebase always
	@echo "--> Activating pre-commit hook"
	pre-commit install
	@echo ""

update-env:
	@echo "--> Installing/updating dependencies"
	pip install -U setuptools pip wheel
	poetry install
	@echo ""

#
# testing
#
test:
	pytest --tb=short

test-with-coverage:
	pytest --tb=short --cov src/$(PKG)

test-long:
	RUN_SLOW_TESTS=True pytest -x

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
	flake8 src *.py

lint-js:
	@echo "--> Linting JavaScript files"
	npx eslint src

format: format-py format-js

format-py:
	docformatter -i -r src
	black src *.py
	@make format-imports

format-imports:
	isort src *.py

format-js:
	npx prettier --write 'abilian/**/*.js'

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
	rm -rf .tox .nox
	rm -rf .eggs
	rm -rf node_modules

update-pot:
	python setup.py extract_messages update_catalog compile_catalog

update-deps:
	poetry update

release:
	maketag
	git push --tags
	poetry publish --build
