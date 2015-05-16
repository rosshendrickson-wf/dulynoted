SHELL := /bin/bash
PYTHON := python
PIP := pip

clean:
	find . -name "*.py[co]" -delete
	rm -f .coverage

run: clean 
	dev_appserver.py .


unit: clean
	nosetests

integrations:
	nosetests --logging-level=ERROR -a slow --with-coverage --cover-package=dulynoted

test: clean integrations

