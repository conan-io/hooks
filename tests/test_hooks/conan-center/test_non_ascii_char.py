import os
import textwrap

from conans import tools
from tests.utils.test_cases.conan_client import ConanClientTestCase


class NonASCIITest(ConanClientTestCase):

    def _get_environ(self, **kwargs):
        kwargs = super(NonASCIITest, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    def test_non_ascii_characters(self):
        conanfile = textwrap.dedent("""\
        from conans import ConanFile
        class AConan(ConanFile):
            {}
            pass
        """)
        tools.save('conanfile.py', content=conanfile.replace("{}", "# Conan, the barbarian"))
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("[NO ASCII CHARACTERS (KB-H047)] OK", output)

        tools.save('conanfile.py', content=conanfile.replace("{}", "# Conan, o bárbaro"))
        output = self.conan(['create', '.', 'name/version@user/test'])
        self.assertIn("ERROR: [NO ASCII CHARACTERS (KB-H047)] The line (3) contains a non-ascii character." \
                      " Only ASCII characters are allowed, please remove it.", output)
