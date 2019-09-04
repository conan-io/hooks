import os
import textwrap

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


class NoPDBsTests(ConanClientTestCase):
    conanfile = textwrap.dedent("""\
        import os
        from conans import ConanFile, tools

        class AConan(ConanFile):
            url = "fake_url.com"
            license = "fake_license"
            description = "whatever"
            
            def package(self):
                tools.save(os.path.join(self.package_folder, "bad.pdb"), "foo")
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(NoPDBsTests, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    def test_pdb_not_allowed(self):
        tools.save('conanfile.py', content=self.conanfile)
        output = self.conan(['create', '.', 'name/version@user/channel'])
        self.assertIn("ERROR: [PDB FILES NOT ALLOWED (KB-H017)]", output)

    def test_no_pdb_is_ok(self):
        tools.save('conanfile.py', content=self.conanfile.replace("bad.pdb", "bad.txt"))
        output = self.conan(['create', '.', 'name/version@user/channel'])
        self.assertNotIn("ERROR: [PDB FILES NOT ALLOWED (KB-H017)]", output)
        self.assertIn("[PDB FILES NOT ALLOWED (KB-H017)] OK", output)
