#!/bin/bash

set -e
set -x

# https://github.com/conan-io/conan_ci_jenkins/blob/master/resources/org/jfrog/conanci/python_runner/conf.py
TEST_FOLDER="${TMPDIR}/${PYVER}"
VENV_FOLDER="${TEST_FOLDER}/venv"
PYENV=/Users/jenkins/.pyenv/bin/pyenv

mkdir -p ${TEST_FOLDER} || echo "ok"

curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash
eval "$(${PYENV} init -)"

case "${PYVER}" in
    py36)
        ${PYENV} install 3.6.12
        ${PYENV} virtualenv 3.6.12 ${VENV_FOLDER}
        ;;
    py37)
        ${PYENV} install 3.7.12
        ${PYENV} virtualenv 3.7.12 ${VENV_FOLDER}
        ;;
    py38)
        ${PYENV} install 3.8.12
        ${PYENV} virtualenv 3.8.12 ${VENV_FOLDER}
        ;;
    py39)
        ${PYENV} install 3.9.2
        ${PYENV} virtualenv 3.9.2 ${VENV_FOLDER}
        ;;
esac

${PYENV} activate ${VENV_FOLDER}
python --version
pip --version
pip install --upgrade pip
pip install --requirement .ci/requirements_macos.txt
python .ci/last_conan_version.py
