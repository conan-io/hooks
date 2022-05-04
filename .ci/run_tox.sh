#!/bin/bash

set -e
set -x

# https://github.com/conan-io/conan_ci_jenkins/blob/master/resources/org/jfrog/conanci/python_runner/conf.py
TEST_FOLDER=${TMPDIR}/${PYVER}

case "${PYVER}" in
    py36)
        PYVER="/Users/jenkins/.pyenv/versions/3.6.13/bin/python"
        ;;
    py37)
        PYVER="/Users/jenkins/.pyenv/versions/3.7.6/bin/python"
        ;;
    py38)
        PYVER="/Users/jenkins/.pyenv/versions/3.8.6/bin/python"
        ;;
    py39)
        PYVER="/Users/jenkins/.pyenv/versions/3.9.0/bin/python"
        ;;
esac

source ${TEST_FOLDER}/bin/activate

${PYVER} -m tox --recreate

