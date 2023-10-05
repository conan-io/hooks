import os
import shutil
import textwrap


from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase
from conan.tools.files import save


class TestKBH007(ConanClientV2TestCase):
    conanfile = textwrap.dedent("""\
                    from conan import ConanFile
                    class AConan(ConanFile):
                        def source(self):
                            pass
                    """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH007, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def test_skip_system_package(self):
        save(self, 'conanfile.py', content=self.conanfile)
        self.conan(['export', '.', '--name=package', '--version=system'])
        output = self.conan(['source', '.', '--name=package', '--version=system'])
        assert "[IMMUTABLE SOURCES (KB-H007)] OK" in output

    def test_no_conandata_yaml(self):
        save(self, 'conanfile.py', content=self.conanfile)
        self.conan(['export', '.', '--name=package', '--version=0.1.0'])
        output = self.conan(['source', '.', '--name=package', '--version=0.1.0'])
        assert "ERROR: [IMMUTABLE SOURCES (KB-H007)] Create a file 'conandata.yml' file with the sources to be downloaded." in output

    def test_no_missing_conandata_but_not_used(self):
        save(self, 'conanfile.py', content=self.conanfile)
        save(self, 'conandata.yml', content="")
        self.conan(['export', '.', '--name=package', '--version=0.1.0'])
        output = self.conan(['source', '.', '--name=package', '--version=0.1.0'])
        assert "ERROR: [IMMUTABLE SOURCES (KB-H007)] Use 'get(self, **self.conan_data" in output

    def test_correct_usage(self):
        conanfile = textwrap.dedent("""\
                       from conan import ConanFile
                       from conan.tools.files import get
                       from conan.errors import ConanException
                       class AConan(ConanFile):

                           def source(self):
                               try:
                                   get(self, **self.conan_data["sources"]["all"], retry=0)
                               except ConanException:
                                   pass    
                       """)
        conandata = textwrap.dedent("""
                    sources:
                        all:
                           url: fakeurl
                           md5: 12323423423
                       """)
        save(self, 'conanfile.py', content=conanfile)
        save(self, 'conandata.yml', content=conandata)
        self.conan(['export', '--name=package', '--version=0.1.0', 'conanfile.py'])
        output = self.conan(['source', '--name=package', '--version=0.1.0', 'conanfile.py'])
        assert "[IMMUTABLE SOURCES (KB-H007)] OK" in output

        conanfile = textwrap.dedent("""\
                       from conan import ConanFile
                       from conan.tools.files import download
                       from conan.errors import ConanException
                       class AConan(ConanFile):

                           def source(self):
                               try:
                                   download(self, self.conan_data["sources"]["all"]["url"], filename="fakepkg", retry=0)
                               except ConanException:
                                   pass
                       """)
        save(self, 'conanfile.py', content=conanfile)
        self.conan(['export', '.', '--name=package', '--version=0.1.0'])
        output = self.conan(['source', '.', '--name=package', '--version=0.1.0'])
        assert "[IMMUTABLE SOURCES (KB-H007)] OK" in output