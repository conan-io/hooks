import os
import textwrap

from tests.utils.test_cases.conan_client import ConanClientTestCase
from tests.utils.compat import save


class NonASCIITests(ConanClientTestCase):
    conanfile = textwrap.dedent("""\
        try:
            from conans import ConanFile
        except ImportError:
            from conan import ConanFile

        class AConan(ConanFile):
            author = "Юрий Алексеевич Гагарин"
            description = "A Terra é Azul"
            license = "fake_license"
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(NonASCIITests, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', 'hooks', 'non_ascii')})
        return kwargs

    def test_with_non_ascii(self):
        save('conanfile.py', content=self.conanfile)
        output = self.conan_export('.', 'name', 'version', 'user', 'channel')
        self.assertIn("ERROR: The file \'conanfile.py\' contains a non-ascii character at line (5)."
                      " Only ASCII characters are allowed, please remove it.", output)

    def test_with_no_non_ascii(self):
        save('conanfile.py', content=self.conanfile
            .replace("Юрий Алексеевич Гагарин", "Yuri Alekseyevich Gagarin")
            .replace("A Terra é Azul", "The Earth is Blue"))
        output = self.conan_export('.', 'name', 'version', 'user', 'channel')
        self.assertNotIn("ERROR:", output)
