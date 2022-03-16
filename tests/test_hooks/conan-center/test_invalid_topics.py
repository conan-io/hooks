import os
import textwrap

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase
from tests.utils.compat import save


class TestInvalidTopics(ConanClientTestCase):
    conanfile = textwrap.dedent("""\
        from conans import ConanFile
        class AConan(ConanFile):
            topics = ("foobar",)
            pass
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(TestInvalidTopics, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    def test_valid_topics(self):
        save('conanfile.py', content=self.conanfile)
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("[INVALID TOPICS (KB-H064)] OK", output)

    def test_no_topics(self):
        save('conanfile.py', content=self.conanfile.replace('topics = ("foobar",)', ""))
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("[INVALID TOPICS (KB-H064)] OK", output)

    def test_invalid_topics(self):
        save('conanfile.py', content=self.conanfile.replace('"foobar",', '"foobar", "conan"'))
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("WARN: [INVALID TOPICS (KB-H064)] The topic 'conan' is invalid and should be"
                      " removed from topics attribute.", output)

    def test_uppercase_topics(self):
        save('conanfile.py', content=self.conanfile.replace('"foobar",', '"foobar", "Baz", "QUX"'))
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("WARN: [INVALID TOPICS (KB-H064)] The topic 'Baz' is invalid; even names "
                      "and acronyms should be formatted entirely in lowercase.", output)
        self.assertIn("WARN: [INVALID TOPICS (KB-H064)] The topic 'QUX' is invalid; even names "
                      "and acronyms should be formatted entirely in lowercase.", output)
