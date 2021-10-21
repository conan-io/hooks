#!/bin/bash

set -e
set -x

eval "$(pyenv init -)"

case "${PYVER}" in
    py36)
        pyenv install 3.6.12
        pyenv virtualenv 3.6.12 conan
        ;;
    py37)
        pyenv install 3.7.12
        pyenv virtualenv 3.7.12 conan
        ;;
    py38)
        pyenv install 3.8.6
        pyenv virtualenv 3.8.6 conan
        ;;
    py39)
        pyenv install 3.9.2
        pyenv virtualenv 3.9.2 conan
        ;;
esac

pyenv activate conan
python --version
pip install --no-cache-dir --upgrade pip
pip3 install --no-cache-dir --requirement .ci/requirements_linux.txt
python .ci/last_conan_version.py
