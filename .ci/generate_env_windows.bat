set PATH=%PATH%;C:/Python36/Scripts/
pip install tox==3.7.0 tox-venv==0.3.1 requests virtualenv
python .ci/last_conan_version.py

IF "%PYVER%"=="py39" (
    set PYVER="Python39"
)
IF "%PYVER%"=="py38" (
    set PYVER="Python38-64"
)
IF "%PYVER%"=="py36" (
    set PYVER="Python36"
)
set TEST_FOLDER=D:/J/t/Hooks/%BUILD_NUMBER%/%PYVER%

virtualenv --python "C:/%PYVER%/python.exe" %TEST_FOLDER% && %TEST_FOLDER%/Scripts/activate && python --version
python -m pip install pip --upgrade
