
PHONY: clean dev setup
export VIRTUAL_ENV ?= $(CURDIR)/venv
export PATH := $(VIRTUAL_ENV)/bin:$(PATH)

setup: venv/pyvenv.cfg
venv/pyvenv.cfg: requirements.txt
	virtualenv -p python3.6 venv && \
	pip install -r requirements.txt && \
	which pip && \
	pip --version && \
	which python && \
	python --version


dev: setup
	env | egrep '(PATH|PY)'
	which python
	which pip
	sam build && \
	sam deploy --config-env devops

qa: setup
	env | egrep '(PATH|PY)'
	which python
	which pip
	sam  build && \
	export HTTPS_PROXY=http://proxy-int.idicore.com:8443 && \
	export NO_PROXY=s3.amazonaws.com,dynamodb.amazonaws.com,169.254.169.254 && \
	env | grep PROXY && \
	sam  deploy --config-env qa


stage: setup
	env | egrep '(PATH|PY)' || true
	which python
	which pip
	pip list | grep sam
	sam build && \
	export HTTPS_PROXY=http://proxy-int.idicore.com:8443 && \
	export NO_PROXY=s3.amazonaws.com,dynamodb.amazonaws.com,169.254.169.254 && \
	sam deploy --config-env stage

prod: setup
	env | egrep '(PATH|PY)'
	which python
	which pip
	pip list | grep sam
	sam build && \
	export HTTPS_PROXY=http://proxy-int.idicore.com:8443 && \
	export NO_PROXY=s3.amazonaws.com,dynamodb.amazonaws.com,169.254.169.254 && \
	env | grep PROXY && \
	sam deploy --config-env prod

#clean will be called seperately in a jenkinsfile
clean:
	rm -rf venv
	rm -rf install

