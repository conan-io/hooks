#!/bin/bash

set -e
set -x

eval "$(pyenv init -)"

case "${PYVER}" in
    py36)
        pyenv install 3.6.13 || true  # Do not fail if already installed
        pyenv virtualenv 3.6.13 ${VIRTUALENV_NAME}
        ;;
    py38)
        pyenv install 3.8.6 || true  # Do not fail if already installed
        pyenv virtualenv 3.8.6 ${VIRTUALENV_NAME}
        ;;
    py39)
        pyenv install 3.9.2 || true  # Do not fail if already installed
        pyenv virtualenv 3.9.2 ${VIRTUALENV_NAME}
        ;;
esac

pyenv activate ${VIRTUALENV_NAME}
python --version
pip install --upgrade pip
pip3 install --requirement tests/requirements_test.txt
pip3 install --requirement .ci/requirements_linux.txt
pip3 install ${CONAN_REQUIREMENT}
conan --version
