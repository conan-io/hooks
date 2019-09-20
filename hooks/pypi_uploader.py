"""Conan hook to upload a Conan Python package also as a pip package to a PyPI repository.

In order to enable this hook do the following:

* add a new Conan attribute called `pypi` in your Conan recipe and set it to `True`
* set the environment variables `TWINE_USERNAME`, `TWINE_PASSWORD` and `TWINE_REPOSITORY`
  to configure `twine` to upload to a PyPI repository.

The hook is copying the whole exported Conan directory into a temporary folder, creating
a setup.py file, creates a source distribution file and uploads the generated package to
a PyPI repository.
"""

import json
import os
import shutil
import subprocess
import tempfile

from urllib.parse import urlparse, urlunsplit
from urllib.request import urlopen
from conans.client import conan_api

SANDBOX_MODULE_FOUND = False
try:
    from setuptools import sandbox

    SANDBOX_MODULE_FOUND = True
except ImportError:
    pass


def get_setup_py_template(**kwargs):
    """Returns the content for a setup.py file based on a template.

    Returns: Content of a setup.py file
    """
    return '''
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The setup script."""

# prevent from normalizing the version in the metadata
from setuptools.extern.packaging import version
version.Version = version.LegacyVersion

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages

setup(
    description="{description}",
    author="conan-io",
    author_email="conan@conan.io",
    license="",
    install_requires=[],
    name="{name}",
    packages=find_packages(),
    version="{version}",
    url="{url}",
    zip_safe=False,
)
'''.format(
        **kwargs
    )


def get_recipe_info(conanfile_path):
    """Returns recipe information via the Conan API.

    Args:
        conanfile_path: Path to conanfile.py

    Returns: recipe info as dictionary
    """
    conan_instance, _, _ = conan_api.Conan.factory()
    # We need to explicitly request attributes since otherwise it will load only Conan default attributes
    # and our custom attribute 'pypi' won't be retrieved.
    recipe_attributes = ["name", "url", "description", "pypi"]
    return conan_instance.inspect(path=conanfile_path, attributes=recipe_attributes)


def _create_setup_py(output, setup_py_path, setup_py_content):
    """Creates a setup.py file which will be used later to upload a pip package.

    Args:
        output: Conan output object to print formatted messages
        setup_py_path: Path to setup.py file
        setup_py_content: Content of setup.py file
    """
    with open(setup_py_path, "wb") as setup_py_fh:
        setup_py_fh.write(setup_py_content.encode("utf-8"))
        output.info("Created %s" % setup_py_path)


def _create_source_distribution(output, setup_py_path):
    """Creates a source distribution by using programmatically setuptools or as an external
    python call

    Args:
        output: Conan output object to print formatted messages
        setup_py_path: Path to setup.py file
    """
    output.info("Running `python setup.py sdist`")
    if SANDBOX_MODULE_FOUND:
        sandbox.run_setup(setup_py_path, ["sdist"])
    else:
        out = subprocess.check_output(["python", setup_py_path, "sdist"])
        output.info(out.decode("utf-8"))


def _upload_to_pypi(output, pypi_username, pypi_password, pypi_repository):
    """Upload the generated source distribution to a PyPI repository

    Args:
        output: Conan output object to print formatted messages
        pypi_username: The username to authenticate to the PyPI repository
        pypi_password: The password to authenticate to the PyPI repository
        pypi_repository: The repository to upload the package to
    """
    output.info("Uploading to '%s'" % (pypi_repository))

    # twine does not have an API to be used from within Python, so let's use
    # it as an external tool.
    out = subprocess.check_output(
        [
            "twine",
            "upload",
            "--verbose",
            "-u",
            pypi_username,
            "-p",
            pypi_password,
            "--repository-url",
            pypi_repository,
            "dist/*",
        ]
    )
    output.info(out.decode("utf-8"))


def _is_package_already_uploaded(pypi_repository, package_name, package_version):
    """Checks whether Python package is already available in PyPI index.

    Args:
        pypi_repository: The repository to search for the package
        package_name: Name of the package to be searched for
        package_version: Version of the package

    Returns: True if package was already uploaded to the PyPI index otherwise false
    """
    parse_result = urlparse(pypi_repository)
    if "/artifactory/api" in parse_result.path:
        artifactory_api_search_url = urlunsplit(
            (
                parse_result.scheme,
                parse_result.netloc,
                "artifactory/api/search/prop",
                "pypi.name=%s&pypi.version=%s" % (package_name, package_version),
                "",
            )
        )
        response = urlopen(artifactory_api_search_url)
        data = json.load(response)
        if response.getcode() == 200 and "results" in data and data["results"]:
            return True
    return False


def post_upload(output, conanfile_path, reference, remote, **kwargs):
    """[Conan hook](https://docs.conan.io/en/latest/reference/hooks.html) called after whole upload
    execution is finished.

    Args:
        output: Conan output object to print formatted messages
        conanfile_path: Path to the conanfile.py file whether it is in local cache or in user space
        reference: Named tuple with attributes name, version, user, and channel
        remote: Named tuple with attributes name, url and verify_ssl
    """
    # Make pylint happy about unused-arguments linter error.
    del remote, kwargs

    recipe_info = get_recipe_info(conanfile_path)
    if "pypi" not in recipe_info:
        output.info(
            "Skipping upload to PyPI repository: 'pypi' attribute not found in Conan project"
        )
        return
    if not bool(recipe_info["pypi"]):
        output.info("Skipping upload to PyPI repository: upload disabled")
        return

    twine_settings = ["TWINE_USERNAME", "TWINE_PASSWORD", "TWINE_REPOSITORY"]
    if not set(twine_settings).issubset(os.environ):
        output.error(
            "Missing Twine configuration. Please define the following environment variables: %s"
            % twine_settings
        )
        return

    # we need to take the version out of the reference since the API returns None only.
    version = reference.version
    package_name = recipe_info["name"]
    template_vars = {
        "url": recipe_info["url"],
        "description": recipe_info["description"],
        "name": package_name,
        "version": version,
    }

    pypi_repository = os.environ["TWINE_REPOSITORY"]

    if not _is_package_already_uploaded(pypi_repository, package_name, version):
        with tempfile.TemporaryDirectory(
            prefix="pypi_uploader_%s" % package_name
        ) as tmp_dir:
            setup_py_dir = os.path.join(tmp_dir, "prj")
            shutil.copytree(
                src=os.path.dirname(os.path.abspath(conanfile_path)), dst=setup_py_dir
            )

            setup_py_path = os.path.join(setup_py_dir, "setup.py")
            setup_py_content = get_setup_py_template(**template_vars)

            os.chdir(setup_py_dir)

            _create_setup_py(output, setup_py_path, setup_py_content)
            _create_source_distribution(output, setup_py_path)
            _upload_to_pypi(
                output,
                pypi_username=os.environ["TWINE_USERNAME"],
                pypi_password=os.environ["TWINE_PASSWORD"],
                pypi_repository=pypi_repository,
            )
            output.success(
                "Package '%s==%s' uploaded to %s"
                % (package_name, version, pypi_repository)
            )
    else:
        output.warn(
            "Package %s==%s is already available in '%s' PyPI index. Upload skipped"
            % (package_name, version, pypi_repository)
        )
