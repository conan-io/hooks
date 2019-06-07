import os
import textwrap

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


class NoLibToolTests(ConanClientTestCase):
    conanfile = textwrap.dedent("""\
        import os
        from conans import ConanFile, tools

        class AConan(ConanFile):
            url = "fake_url.com"
            license = "fake_license"
            description = "whatever"
            
            def package(self):
                tools.save(os.path.join(self.package_folder, "bad.la"), "foo")
                tools.save(os.path.join(self.package_folder, "bad.lab"), "foo")
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(NoLibToolTests, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    def test_libtool_not_allowed(self):
        tools.save('conanfile.py', content=self.conanfile)
        output = self.conan(['create', '.', 'name/version@user/channel'])
        self.assertIn("ERROR: [LIBTOOL FILES PRESENCE]", output)
        self.assertIn("bad.la", output)
