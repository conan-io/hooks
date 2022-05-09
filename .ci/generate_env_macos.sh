#!/bin/bash

set -e
set -x

# https://github.com/conan-io/conan_ci_jenkins/blob/master/resources/org/jfrog/conanci/python_runner/conf.py
TEST_FOLDER="${TMPDIR}/${PYVER}"
VENV_FOLDER="${TEST_FOLDER}/venv"
PYENV_ROOT="${TEST_FOLDER}/pyenv"
PYENV="${PYENV_ROOT}/.pyenv/bin/pyenv"

mkdir -p ${TEST_FOLDER} || echo "ok"

curl -s -L -o "${TEST_FOLDER}/pyenv-installer" https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer
chmod +x "${TEST_FOLDER}/pyenv-installer"
PYENV_ROOT=${PYENV_ROOT} "${TEST_FOLDER}/pyenv-installer"
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
    py310)
        ${PYENV} install 3.10.4
        ${PYENV} virtualenv 3.10.4 ${VENV_FOLDER}
        ;;
esac

${PYENV} activate ${VENV_FOLDER}
python --version
pip --version
pip install --upgrade pip
pip install --requirement .ci/requirements_macos.txt
python .ci/last_conan_version.py
