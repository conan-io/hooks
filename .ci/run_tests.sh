#!/bin/bash

set -e
set -x

# https://github.com/conan-io/conan_ci_jenkins/blob/master/resources/org/jfrog/conanci/python_runner/conf.py
TEST_FOLDER=${WORKSPACE}/${PYVER}

case "${PYVER}" in
    py36)
        PYVER="/Users/jenkins/.pyenv/versions/3.6.15/bin/python"
        ;;
    py38)
        PYVER="/Users/jenkins/.pyenv/versions/3.8.12/bin/python"
        ;;
    py39)
        PYVER="/Users/jenkins/.pyenv/versions/3.9.11/bin/python"
        ;;
esac

source ${TEST_FOLDER}/bin/activate

python -m pytest ./tests ${PYTEST_ARGS}
