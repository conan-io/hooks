# coding=utf-8

import os
import textwrap
import unittest

from conans import tools
from tests.utils.test_cases.conan_client import ConanClientTestCase

here = os.path.dirname(__file__)


class CMakeCxxStd(ConanClientTestCase):
    conanfile = textwrap.dedent("""
        from conans import ConanFile

        class AConan(ConanFile):
            exports_sources = "CMakeLists.txt"
            pass
    """)
    cmakefile = textwrap.dedent("""
        cmake_minimum_required(VERSION 3.8)
        project(foobar)
        add_library(foobar ...)
        target_compile_features(foobar PUBLIC cxx_std_11)
    """)

    def _get_environ(self, **kwargs):
        kwargs = super(CMakeCxxStd, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(here, '..', '..', '..', 'hooks', 'conan-center')})
        return kwargs

    def test_no_cmakefile(self):
        tools.save('conanfile.py', content=self.conanfile)
        output = self.conan(['export', '.', 'name/version@user/testing'])
        self.assertIn("[CMAKE REQUIRED VERSION - CXX_STD (KB-H063)] OK", output)

    def test_supported_version(self):
        tools.save('conanfile.py', content=self.conanfile)
        tools.save('CMakeLists.txt', content=self.cmakefile)
        tools.save('test_package/CMakeLists.txt', content=self.cmakefile)
        output = self.conan(['export', '.', 'name/version@user/testing'])
        self.assertIn("[CMAKE REQUIRED VERSION - CXX_STD (KB-H063)] OK", output)

    def test_outdated_version(self):
        tools.save('conanfile.py', content=self.conanfile)
        tools.save('CMakeLists.txt', content=self.cmakefile.replace("3.8", "3.1"))
        output = self.conan(['export', '.', 'name/version@user/testing'])
        self.assertIn("ERROR: [CMAKE REQUIRED VERSION - CXX_STD (KB-H063)] The "
                      "CMAKE_CXX_KNOWN_FEATURES (cxx_std_11) requires CMake 3.8 at least. "
                      "Update the CMakeLists.txt for minimum version required.", output)

    def test_outdated_test_package(self):
        tools.save('conanfile.py', content=self.conanfile)
        tools.save('CMakeLists.txt', content=self.cmakefile)
        tools.save('test_package/CMakeLists.txt', content=self.cmakefile.replace("3.8", "3.1"))
        output = self.conan(['export', '.', 'name/version@user/testing'])
        self.assertIn("ERROR: [CMAKE REQUIRED VERSION - CXX_STD (KB-H063)] The "
                      "CMAKE_CXX_KNOWN_FEATURES (cxx_std_11) requires CMake 3.8 at least. "
                      "Update the CMakeLists.txt for minimum version required.", output)

    def test_newer_cmake_version(self):
        tools.save('conanfile.py', content=self.conanfile)
        tools.save('CMakeLists.txt', content=self.cmakefile.replace("3.8", "3.18"))
        output = self.conan(['export', '.', 'name/version@user/testing'])
        self.assertIn("[CMAKE REQUIRED VERSION - CXX_STD (KB-H063)] OK", output)
