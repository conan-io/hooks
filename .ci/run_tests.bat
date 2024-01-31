REM https://github.com/conan-io/conan_ci_jenkins/blob/master/resources/org/jfrog/conanci/python_runner/conf.py
set TEST_FOLDER=%WORKSPACE%/%PYVER%

call %TEST_FOLDER%/Scripts/activate && python -m pytest %PYTEST_ARGS%
