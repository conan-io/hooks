set PATH=%PATH%;C:/Python36/Scripts/
pip install --timeout 100 --retries 10 requests virtualenv

set TEST_FOLDER=%WORKSPACE%/%PYVER%

IF "%PYVER%"=="py39" (
    set PYVER="Python39"
)
IF "%PYVER%"=="py38" (
    set PYVER="Python38-64"
)
IF "%PYVER%"=="py36" (
    set PYVER="Python36"
)


virtualenv --python "C:/%PYVER%/python.exe" %TEST_FOLDER% && %TEST_FOLDER%/Scripts/activate &&^
python --version && ^
python -m pip install pip --upgrade && ^
python -m pip install --requirement tests/requirements_test.txt && ^
python -m pip install %CONAN_REQUIREMENT% && ^
conan --version
