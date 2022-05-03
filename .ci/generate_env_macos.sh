#!/bin/bash

set -e
set -x

# https://github.com/conan-io/conan_ci_jenkins/blob/master/resources/org/jfrog/conanci/python_runner/conf.py

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

TEST_FOLDER=${TMPDIR}/${PYVER}
mkdir -p ${TEST_FOLDER} || echo "ok"
${PYVER} -m pip install tox tox-venv requests virtualenv
${PYVER} -m virtualenv --python ${PYVER} ${TEST_FOLDER} && \
  source ${TEST_FOLDER}/bin/activate && \
  python --version && \
  python -m pip install --upgrade pip && \
  python -m pip install --requirement .ci/requirements_macos.txt && \
  python .ci/last_conan_version.py

