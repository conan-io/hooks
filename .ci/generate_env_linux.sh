#!/bin/bash

set -e
set -x

eval "$(pyenv init -)"

case "${PYVER}" in
    py27)
        pyenv install 2.7.18
        pyenv virtualenv 2.7.18 conan
        ;;
    py36)
        pyenv install 3.6.14
        pyenv virtualenv 3.6.14 conan
        ;;
    py37)
        pyenv install 3.7.11
        pyenv virtualenv 3.7.11 conan
        ;;
    py38)
        pyenv install 3.8.11
        pyenv virtualenv 3.8.11 conan
        ;;
    py39)
        pyenv install 3.9.6
        pyenv virtualenv 3.9.6 conan
        ;;
esac

pyenv activate conan
python --version
pip install --upgrade pip
pip3 install --requirement .ci/requirements_linux.txt
python .ci/last_conan_version.py
