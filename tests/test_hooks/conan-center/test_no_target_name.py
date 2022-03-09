import os
import textwrap
import pytest

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase
from tests.utils.compat import save


class TestNoTargetName(ConanClientTestCase):
    conanfile = textwrap.dedent("""\
                from conans import ConanFile
                class AConan(ConanFile):
                    def package_info(self):
                        {}

                """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestNoTargetName, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    def test_with_name(self):
        save('conanfile.py', content=self.conanfile.replace("{}", 'self.cpp_info.name = "Foo"'))
        output = self.conan(['export', '.', 'name/version@user/test'])
        self.assertIn("ERROR: [NO TARGET NAME (KB-H040)] CCI uses the name of the package for cmake generator and "
                      "filename by default. Replace 'cpp_info.name' by 'cpp_info.names[<generator>]'.", output)

    def test_with_filename(self):
        save('conanfile.py', content=self.conanfile.replace("{}", 'self.cpp_info.filename = "Foobar"'))
        output = self.conan(['export', '.', 'name/version@user/test'])
        self.assertIn("ERROR: [NO TARGET NAME (KB-H040)] CCI uses the name of the package for cmake generator and "
                      "filename by default. Replace 'cpp_info.filename' by 'cpp_info.filenames[<generator>]'.", output)

    def test_with_cmake_generator(self):
        save('conanfile.py', content=self.conanfile.replace("{}", 'self.cpp_info.names["cmake"] = "Foo"'))
        output = self.conan(['export', '.', 'name/version@user/test'])
        self.assertIn("ERROR: [NO TARGET NAME (KB-H040)] CCI uses the name of the package for cmake generator. "
                      "Conanfile should not contain 'self.cpp_info.names['cmake']'. "
                      "Use 'cmake_find_package' and 'cmake_find_package_multi' instead.", output)

    def test_with_cmake_multi_generator(self):
        save('conanfile.py', content=self.conanfile.replace("{}", 'self.cpp_info.names["cmake_multi"] = "Foo"'))
        output = self.conan(['export', '.', 'name/version@user/test'])
        self.assertIn("ERROR: [NO TARGET NAME (KB-H040)] CCI uses the name of the package for cmake_multi generator. "
                      "Conanfile should not contain 'self.cpp_info.names['cmake_multi']'. "
                      "Use 'cmake_find_package' and 'cmake_find_package_multi' instead.", output)

    def test_with_pkg_config(self):
        save('conanfile.py', content=self.conanfile.replace("{}", 'self.cpp_info.names["pkg_config"] = "foolib"'))
        output = self.conan(['export', '.', 'name/version@user/test'])
        self.assertIn("[NO TARGET NAME (KB-H040)] OK", output)

    def test_with_cmake_find_package(self):
        save('conanfile.py', content=self.conanfile.replace("{}", 'self.cpp_info.names["cmake_find_package"] = '
                                                                        '"foolib"'))
        output = self.conan(['export', '.', 'name/version@user/test'])
        self.assertIn("[NO TARGET NAME (KB-H040)] OK", output)

    def test_with_cmake_find_package_multi(self):
        save('conanfile.py', content=self.conanfile.replace("{}", 'self.cpp_info.names'
                                                                        '["cmake_find_package_multi"] = "foolib"'))
        output = self.conan(['export', '.', 'name/version@user/test'])
        self.assertIn("[NO TARGET NAME (KB-H040)] OK", output)
