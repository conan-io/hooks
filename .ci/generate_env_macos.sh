#!/bin/bash

set -e
set -x

# https://github.com/conan-io/conan_ci_jenkins/blob/master/resources/org/jfrog/conanci/python_runner/conf.py
TEMP_FOLDER=`mktemp -d`
TEST_FOLDER="${TEMP_FOLDER}/${PYVER}"
VENV_FOLDER="${TEST_FOLDER}/venv"
PYENV_ROOT="${TEMP_FOLDER}/pyenv"
PYENV="${PYENV_ROOT}/bin/pyenv"
export PATH="${PYENV_ROOT}/bin:$PATH"

mkdir -p ${TEST_FOLDER} || echo "ok"
export PYENV_ROOT=${PYENV_ROOT}

curl -s -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash
eval "$(pyenv init --path)"
eval "$(pyenv virtualenv-init -)"

case "${PYVER}" in
    py36)
        pyenv install 3.6.12
        pyenv virtualenv 3.6.12 ${VENV_FOLDER}
        ;;
    py37)
        pyenv install 3.7.12
        pyenv virtualenv 3.7.12 ${VENV_FOLDER}
        ;;
    py38)
        pyenv install 3.8.12
        pyenv virtualenv 3.8.12 ${VENV_FOLDER}
        ;;
    py39)
        pyenv install 3.9.2
        pyenv virtualenv 3.9.2 ${VENV_FOLDER}
        ;;
    py310)
        pyenv install 3.10.4
        pyenv virtualenv 3.10.4 ${VENV_FOLDER}
        ;;
esac

pyenv activate "${VENV_FOLDER}"
python --version
pip --version
pip install --upgrade pip
pip install --requirement .ci/requirements_macos.txt
python .ci/last_conan_version.py
