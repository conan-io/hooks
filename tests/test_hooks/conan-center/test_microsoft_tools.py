import os
import textwrap

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


class MSVCToolsTests(ConanClientTestCase):
    conanfile_outdated = textwrap.dedent("""\
        import os
        from conans import ConanFile, tools

        class AConan(ConanFile):
            url = "fake_url.com"
            license = "fake_license"
            description = "whatever"
            settings = "os", "arch", "build_type", "compiler"

            @property
            def _is_msvc(self):
                return self.settings.compiler == "Visual Studio" or self.settings.compiler == "msvc"

            def validate(self):
                if self._is_msvc:
                    self.output.info("It's MSVC")
        """)

    conanfile_modern = textwrap.dedent("""\
            import os
            from conan import ConanFile
            from conan.tools.microsoft import is_msvc

            class AConan(ConanFile):
                url = "fake_url.com"
                license = "fake_license"
                description = "whatever"
                settings = "os", "arch", "build_type", "compiler"

                def validate(self):
                    if is_msvc(self):
                        self.output.info("It's MSVC")
            """)

    def _get_environ(self, **kwargs):
        kwargs = super(MSVCToolsTests, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    def test_custom_is_msvc_not_allowed(self):
        tools.save('conanfile.py', content=self.conanfile_outdated)
        output = self.conan(['create', '.', 'name/version@user/channel'])
        self.assertIn("WARN: [MICROSOFT TOOLS (KB-H072)]", output)
        self.assertIn("conanfile.py:12 Custom deprecated functions detected. Use of '_is_msvc' is outdated, replace by 'conan.tools.microsoft.is_msvc'.", output)

    def test_tools_msvc(self):
        tools.save('conanfile.py', content=self.conanfile_modern)
        output = self.conan(['create', '.', 'name/version@user/channel'])
        self.assertIn("[MICROSOFT TOOLS (KB-H072)] OK", output)
