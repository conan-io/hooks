import os
import textwrap
import shutil
import platform
import pytest
from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase
from conan.tools.files import save


class TestKBH027(ConanClientV2TestCase):
    conanfile = textwrap.dedent("""\
                from conan import ConanFile
                class AConan(ConanFile):
                    exports = "foo."
                """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH027, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    @pytest.mark.skipif(platform.system() == "Windows", reason="Can not use illegal name on Windows")
    def test_regular_filename(self):
        save(self, 'conanfile.py', content=self.conanfile)
        output = self.conan(['export', 'conanfile.py', '--name=name', '--version=0.1.0'])
        assert "[FILE CONSISTENCY (KB-H027)] OK" in output

    @pytest.mark.skipif(platform.system() == "Windows", reason="Can not use illegal name on Windows")
    def test_disallowed_characters(self):
        save(self, "conan+file.py", content=self.conanfile)
        self.conan(['export', '--name=name', '--version=0.1.0', "conan+file.py"], expected_return_code=1)

    @pytest.mark.skipif(platform.system() == "Windows", reason="Can not use illegal name on Windows")
    def test_ends_with_dot(self):
        save(self, "conanfile.py", content=self.conanfile)
        save(self, "foo.", content="")
        output = self.conan(['export', "conanfile.py", '--name=name', '--version=0.1.0'])
        assert "ERROR: [FILE CONSISTENCY (KB-H027)] The file 'foo.' ends with a dot" in output