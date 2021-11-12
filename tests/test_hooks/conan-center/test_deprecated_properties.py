import os
import textwrap

import pytest
from conans import tools
from parameterized import parameterized


from tests.utils.test_cases.conan_client import ConanClientTestCase


class TestDeprecatedProperties(ConanClientTestCase):
    conanfile = textwrap.dedent("""\
        from conans import ConanFile
        class AConan(ConanFile):
            def package_info(self):
                {}
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestDeprecatedProperties, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    @parameterized.expand([
        'self.cpp_info.names["cmake_find_package_multi"] = "myname"',
        'self.cpp_info.components["mycomp"].names["cmake_find_package_multi"] = "myname"',
        'self.cpp_info.filenames["cmake_find_package_multi"] = "myname"',
        'self.cpp_info.components["mycomp"].filenames["cmake_find_package_multi"] = "myname"',
        'self.cpp_info.build_modules["cmake_find_package_multi"] = "myname"',
        'self.cpp_info.build_modules = ["/my/path/m.cmake", "my/other/path/m2.cmake"]',
    ])
    def test_deprecated_properties(self, pkg_info_line):
        tools.save('conanfile.py', content=self.conanfile.format(pkg_info_line))
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("[DEPRECATED NAMES, FILENAMES AND BUILD_MODULES (KB-H065)] Using 'names', "
                      "'filenames' and 'build_modules' is deprecated from Conan 1.42. "
                      "Use 'set_property' and 'get_property' methods of the cpp_info object instead.", output)

    @parameterized.expand([
        'self.cpp_info.set_property("cmake_file_name", "MyFileName")',
        'self.cpp_info.set_property("cmake_target_name", "MyTargetName")',
        'self.cpp_info.components["mycomp"].set_property("cmake_target_name", "mycomponent-name")',
        'self.cpp_info.components["mycomp"].set_property("cmake_build_modules", ["lib/m2.cmake", "lib/m3.cmake"])',
        'self.cpp_info.components["mycomp"].set_property("pkg_config_name", "mypkg-config-name")',
        'self.cpp_info.components["mycomp"].set_property("custom_name", "mycomponent-name", "custom_generator")',
    ])
    def test_valid_properties(self, pkg_info_line):
        tools.save('conanfile.py', content=self.conanfile.format(pkg_info_line))
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("[DEPRECATED NAMES, FILENAMES AND BUILD_MODULES (KB-H065)] OK", output)
