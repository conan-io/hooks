#!/bin/bash

set -e
set -x

eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
eval "$(pyenv init --path)"

case "${PYVER}" in
    py27)
        pyenv install 2.7.17
        pyenv virtualenv 2.7.17 conan
        ;;
    py33)
        pyenv install 3.3.7
        pyenv virtualenv 3.3.7 conan
        ;;
    py34)
        pyenv install 3.4.10
        pyenv virtualenv 3.4.10 conan
        ;;
    py35)
        pyenv install 3.5.9
        pyenv virtualenv 3.5.9 conan
        ;;
    py36)
        pyenv install 3.6.10
        pyenv virtualenv 3.6.10 conan
        ;;
    py37)
        pyenv install 3.7.6
        pyenv virtualenv 3.7.6 conan
        ;;
    py38)
        pyenv install 3.8.1
        pyenv virtualenv 3.8.1 conan
        ;;

esac

pyenv rehash
pyenv activate conan
python --version
pip3 install --requirement .ci/requirements_linux.txt
python .ci/last_conan_version.py
