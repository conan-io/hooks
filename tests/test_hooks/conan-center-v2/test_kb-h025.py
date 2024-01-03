import os
import textwrap
import shutil
from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase
from conan.tools.files import save


class TestKBH025(ConanClientV2TestCase):

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH025, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def test_no_duplicated_requires(self):
        conanfile = textwrap.dedent("""\
            from conan import ConanFile
            class MockRecipe(ConanFile):
                requires = "foo/0.1.0"                
            """)

        save(self, 'conanfile.py', content=conanfile)
        output = self.conan(['export', '.', '--name=name', '--version=0.1.0'])
        assert "[SINGLE REQUIRES (KB-H025)]" in output

    def test_duplicated_requires(self):
        conanfile = textwrap.dedent("""\
            from conan import ConanFile
            class MockRecipe(ConanFile):
                requires = "foo/0.1.0"
                def requirements(self):
                    self.requires("bar/0.1.0")
            """)

        save(self, 'conanfile.py', content=conanfile)
        output = self.conan(['export', '.', '--name=name', '--version=0.1.0'])
        assert "ERROR: [SINGLE REQUIRES (KB-H025)] Both 'requires' attribute and 'requirements()' method should not be declared at same recipe" in output

    def test_duplicated_tool_requires(self):
        conanfile = textwrap.dedent("""\
                from conan import ConanFile
                class MockRecipe(ConanFile):
                    tool_requires = "foo/0.1.0"
                    def build_requirements(self):
                        self.tool_requires("bar/0.1.0")
                """)

        save(self, 'conanfile.py', content=conanfile)
        output = self.conan(['export', '.', '--name=name', '--version=0.1.0'])
        assert "ERROR: [SINGLE REQUIRES (KB-H025)] Both 'build_requires' attribute and 'build_requirements()' method should not be declared at same recipe" in output