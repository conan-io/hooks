import os
import textwrap

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


class InvalidSymlinksTestCase(ConanClientTestCase):
    conanfile = textwrap.dedent("""\
        import os
        from conans import ConanFile, tools

        class AConan(ConanFile):

            def build(self):
                tools.save(os.path.join(self.build_folder, "build.txt"), "contents")

            def package(self):
                os.symlink(os.path.join(self.build_folder, "build.txt"),
                           os.path.join(self.package_folder, "outside_symlink.txt"))
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(NoPDBsTests, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    def test_symlink_invalid(self):
        tools.save('conanfile.py', content=self.conanfile)
        output = self.conan(['create', '.', 'name/version@user/channel'])
        self.assertIn("ERROR: [INVALID SYMLINKS (KB-H049)]", output)
