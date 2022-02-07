import os
import textwrap

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


class ToolsOSInfoTest(ConanClientTestCase):
    def _get_environ(self, **kwargs):
        kwargs = super(ToolsOSInfoTest, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    def test_config_options(self):
        conanfile = textwrap.dedent("""\
        from conans import ConanFile, tools
        class AConan(ConanFile):
            def config_options(self):
                if tools.os_info.is_windows:
                    pass
        """)
        tools.save('conanfile.py', content=conanfile)
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("ERROR: [NO OS_INFO (KB-H066)]", output)

    def test_configure(self):
        conanfile = textwrap.dedent("""\
        from conans import ConanFile, tools
        class AConan(ConanFile):
            def configure(self):
                if tools.os_info.is_linux:
                    pass
        """)
        tools.save('conanfile.py', content=conanfile)
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("ERROR: [NO OS_INFO (KB-H066)]", output)

    def test_import(self):
        conanfile = textwrap.dedent("""\
        from conans import ConanFile
        from conans.tools import os_info
        class AConan(ConanFile):
            def configure(self):
                if os_info.is_macos:
                    pass
        """)
        tools.save('conanfile.py', content=conanfile)
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("ERROR: [NO OS_INFO (KB-H066)]", output)
