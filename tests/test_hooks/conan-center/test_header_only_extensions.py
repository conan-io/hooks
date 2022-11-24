import os
import textwrap

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


class TestHeaderOnlyExtensions(ConanClientTestCase):
    """
    False positive from https://github.com/conan-io/conan-center-index/pull/14330
    post_package(): ERROR: [STATIC ARTIFACTS (KB-H074)] Package with 'shared=False' option did not contain any static artifact
    """

    conanfile = textwrap.dedent("""\
        from conan import ConanFile
        from conan.tools.cmake import cmake_layout
        from conan.tools.layout import basic_layout
        import os
        
        class MiniaudioConan(ConanFile):
            name = "miniaudio"
            settings = "os", "arch", "compiler", "build_type"
            options = {
                "shared": [True, False],
                "fPIC": [True, False],
                "header_only": [True, False],
            }
            default_options = {
                "shared": False,
                "fPIC": True,
                "header_only": True,
            }
        
            def layout(self):
                if self.options.header_only:
                    basic_layout(self, src_folder="src")
                else:
                    cmake_layout(self, src_folder="src")
        
            def package_id(self):
                if self.options.header_only:
                    self.info.clear()
        
            def package_info(self):
                if self.options.header_only:
                    self.cpp_info.bindirs = []
                    self.cpp_info.libdirs = []
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestHeaderOnlyExtensions, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    def test_create_header_only(self):
        tools.save('conanfile.py', content=self.conanfile)
        output = self.conan(['create', '.', 'miniaudio/0.11.11@', '-o', 'miniaudio:header_only=True'])
        self.assertIn("[STATIC ARTIFACTS (KB-H074)] OK", output)
