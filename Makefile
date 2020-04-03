.PHONY: dockerfile
dockerfile:
	docker build -t canyan/canyan-tester:master .

.PHONY: venv
venv:
	virtualenv -p python3 venv

.PHONY: setup
setup:
	pip install -r requirements.txt
	pip install --editable .

.PHONY: dist
dist:
	python3 setup.py sdist bdist_wheel

.PHONY: clean
clean:
	rm -fr build dist canyantester.egg-info

.PHONY: check
check: black flake8 mypy pylint pycodestyle

.PHONY: test
test:
	py.test -p no:warnings

.PHONY: black
black:
	black --skip-string-normalization canyantester

.PHONY: flake8
flake8:
	flake8 --ignore=E501,E402,W503 canyantester

.PHONY: mypy
mypy:
	mypy canyantester

.PHONY: pylint
pylint:
	pylint canyantester

.PHONY: pycodestyle
pycodestyle:
	pycodestyle --ignore=E501,W503,E402,E701 canyantester

.PHONY: coverage
coverage:
	coverage run -m py.test -p no:warnings
	coverage report
	coverage html
	coverage xml
