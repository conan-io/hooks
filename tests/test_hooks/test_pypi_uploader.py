"""Unit tests for pypi_uploader hook.
"""

import os
import sys

from unittest.mock import ANY, MagicMock, patch
from hamcrest import contains_string, match_equality
import pytest

from conans.model.ref import ConanFileReference

# We don't want to mess up the hooks directory with some __init__.py files and
# therefore add the path to the hooks manually in the test
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from hooks import pypi_uploader


def conan_recipe_with_pypi(pypi_attribute_value):
    """Returns a conan recipe info dict object with a specific value for the 'pypi' attribute.

    Args:
        pypi_attribute_value: Value of 'pypi' attribute (eg. True, False, 0, 1)

    Returns: a recipe info dict object
    """
    return {
        "name": "abc",
        "url": "https://abc.acme.org",
        "description": "abc description",
        "pypi": pypi_attribute_value,
    }


def conan_recipe_without_pypi_attr_set():
    """Returns a conan recipe info dict object without the 'pypi' attribute.

    Returns: a recipe info dict object
    """
    return {
        "name": "abc",
        "url": "https://abc.acme.org",
        "description": "abc description",
    }


def with_configured_twine():
    """Set environment variable to configure twine for upload
    """
    os.environ["TWINE_REPOSITORY"] = "https://twine.repo"
    os.environ["TWINE_USERNAME"] = "user"
    os.environ["TWINE_PASSWORD"] = "pwd"


@patch("hooks.pypi_uploader.get_recipe_info")
@patch("subprocess.check_output")
def test_should_not_upload_since_pypi_attr_not_set_in_project(
    mock_upload_to_pypi_subprocess, mock_get_recipe_info
):
    """Expects to print only an info message that the 'pypi' attribute on the Conan project is not set.
    """
    # Given
    mock_output = MagicMock()
    mock_conanfile_path = MagicMock()
    mock_reference = MagicMock()
    mock_remote = MagicMock()
    mock_get_recipe_info.return_value = conan_recipe_without_pypi_attr_set()

    # When
    pypi_uploader.post_upload(
        output=mock_output,
        conanfile_path=mock_conanfile_path,
        reference=mock_reference,
        remote=mock_remote,
    )

    # Then
    mock_output.info.assert_called_with(
        "Skipping upload to PyPI repository: 'pypi' attribute not found in Conan project"
    )
    mock_upload_to_pypi_subprocess.assert_not_called()


@pytest.mark.parametrize("test_input", [False, 0])
@patch("hooks.pypi_uploader.get_recipe_info")
@patch("subprocess.check_output")
def test_should_not_upload_since_pypi_attr_disabled(
    mock_upload_to_pypi_subprocess, mock_get_recipe_info, test_input
):
    """Expects to print only an info message that the PyPI upload is disabled.
    """
    # Given
    mock_output = MagicMock()
    mock_conanfile_path = MagicMock()
    mock_reference = MagicMock()
    mock_remote = MagicMock()
    mock_get_recipe_info.return_value = conan_recipe_with_pypi(test_input)

    # When
    pypi_uploader.post_upload(
        output=mock_output,
        conanfile_path=mock_conanfile_path,
        reference=mock_reference,
        remote=mock_remote,
    )

    # Then
    mock_output.info.assert_called_with(
        "Skipping upload to PyPI repository: upload disabled"
    )
    mock_upload_to_pypi_subprocess.assert_not_called()


@patch("hooks.pypi_uploader.get_recipe_info")
@patch("subprocess.check_output")
def test_should_inform_about_missing_twine_configuration(
    mock_upload_to_pypi_subprocess, mock_get_recipe_info
):
    """Expects to print an error message that twine environment variables are missing.
    """
    # Given
    mock_output = MagicMock()
    mock_conanfile_path = MagicMock()
    mock_reference = MagicMock()
    mock_remote = MagicMock()
    mock_get_recipe_info.return_value = conan_recipe_with_pypi(True)

    # When
    pypi_uploader.post_upload(
        output=mock_output,
        conanfile_path=mock_conanfile_path,
        reference=mock_reference,
        remote=mock_remote,
    )

    # Then
    mock_output.error.assert_called_with(
        match_equality(
            contains_string(
                "Missing Twine configuration. Please define the following environment variables"
            )
        )
    )
    mock_upload_to_pypi_subprocess.assert_not_called()


@patch("hooks.pypi_uploader.get_recipe_info")
@patch("hooks.pypi_uploader._is_package_already_uploaded")
@patch("subprocess.check_output")
def test_should_inform_that_upload_is_skipped_if_package_is_already_uploaded(
    mock_upload_to_pypi_subprocess, mock_is_package_uploaded, mock_get_recipe_info
):
    """Expect that upload to PyPI is skipped
    """
    # Given
    mock_output = MagicMock()
    mock_conanfile_path = "/abc/conanfile.py"

    mock_reference = ConanFileReference.loads("abc/1.2.3@ci/stable")
    mock_remote = MagicMock()
    mock_get_recipe_info.return_value = conan_recipe_with_pypi(True)
    mock_is_package_uploaded.return_value = True

    with_configured_twine()

    # When
    pypi_uploader.post_upload(
        output=mock_output,
        conanfile_path=mock_conanfile_path,
        reference=mock_reference,
        remote=mock_remote,
    )

    # Then
    mock_is_package_uploaded.assert_called_with("https://twine.repo", "abc", "1.2.3")
    mock_output.warn.assert_called_with(
        match_equality(contains_string("Upload skipped"))
    )
    mock_upload_to_pypi_subprocess.assert_not_called()


@patch("hooks.pypi_uploader.get_recipe_info")
@patch("hooks.pypi_uploader._create_setup_py")
@patch("hooks.pypi_uploader._create_source_distribution")
@patch("hooks.pypi_uploader._is_package_already_uploaded")
@patch("tempfile.TemporaryDirectory")
@patch("shutil.copytree")
@patch("os.chdir")
@patch("subprocess.check_output")
# pylint: disable=too-many-arguments
def test_should_call_twine_to_upload_package_to_pypi_repo(
    mock_upload_to_pypi_subprocess,
    mock_chdir,
    mock_copytree,
    mock_tmpdir,
    mock_is_package_uploaded,
    mock_create_source_dist,
    mock_create_setup_py,
    mock_get_recipe_info,
):
    """Expect that upload to PyPI is not skipped
    """
    # Given
    mock_output = MagicMock()
    mock_conanfile_path = "/abc/conanfile.py"
    mock_reference = ConanFileReference.loads("abc/1.2.3@ci/stable")
    mock_remote = MagicMock()

    mock_tmpdir.return_value.__enter__.return_value = "/tmp/my_tmp_dir"
    # mock_chdir.return_value = "/"
    mock_get_recipe_info.return_value = conan_recipe_with_pypi(True)
    mock_is_package_uploaded.return_value = False

    with_configured_twine()

    # When
    pypi_uploader.post_upload(
        output=mock_output,
        conanfile_path=mock_conanfile_path,
        reference=mock_reference,
        remote=mock_remote,
    )

    # Then
    mock_copytree.assert_called_with(
        src="/abc",
        dst=os.path.join(mock_tmpdir.return_value.__enter__.return_value, "prj"),
    )
    mock_chdir.assert_called_with("/tmp/my_tmp_dir/prj")
    mock_create_setup_py.assert_called_with(
        mock_output, "/tmp/my_tmp_dir/prj/setup.py", ANY
    )
    mock_create_source_dist.assert_called_with(
        mock_output, "/tmp/my_tmp_dir/prj/setup.py"
    )
    mock_is_package_uploaded.assert_called_with("https://twine.repo", "abc", "1.2.3")
    mock_upload_to_pypi_subprocess.assert_called_with(
        [
            "twine",
            "upload",
            "--verbose",
            "-u",
            "user",
            "-p",
            "pwd",
            "--repository-url",
            "https://twine.repo",
            "dist/*",
        ]
    )
    mock_tmpdir.return_value.__exit__.assert_called_once()
