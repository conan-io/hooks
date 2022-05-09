#!/bin/bash

set -e
set -x

# https://github.com/conan-io/conan_ci_jenkins/blob/master/resources/org/jfrog/conanci/python_runner/conf.py
TEST_FOLDER="${TMPDIR}/${PYVER}"
VENV_FOLDER="${TEST_FOLDER}/venv"

mkdir -p ${TEST_FOLDER} || echo "ok"

brew update
brew install pyenv
eval "$(pyenv init -)"

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
esac

pyenv activate ${VENV_FOLDER}
python --version
pip install --upgrade pip
pip3 install --requirement .ci/requirements_macos.txt
python .ci/last_conan_version.py
