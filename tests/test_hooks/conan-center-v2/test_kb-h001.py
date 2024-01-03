import os
import shutil
import textwrap

from conan.tools.files import save

from tests.utils.test_cases.conan_client_v2 import ConanClientV2TestCase


class TestKBH001(ConanClientV2TestCase):
    conanfile_empty = textwrap.dedent("""\
        from conan import ConanFile
        class AConan(ConanFile):
           {placeholder}
           pass

        """)
    conanfile_base = textwrap.dedent("""\
            from conan import ConanFile
            class AConan(ConanFile):
                name = "name"
                url = "https://github.com/conan-io/conan-center-index"
                license = "fake_license"
                description = "whatever"
                homepage = "homepage.com"
                topics = ("fake_topic", "another_fake_topic")                
                {placeholder}
            """)

    bad_recipe_output = [
        "ERROR: [RECIPE METADATA (KB-H001)] The mandatory attribute 'url' is missing. Please, add it to the recipe.",
        "ERROR: [RECIPE METADATA (KB-H001)] The mandatory attribute 'license' is missing. Please, add it to the recipe.",
        "ERROR: [RECIPE METADATA (KB-H001)] The mandatory attribute 'description' is missing. Please, add it to the recipe.",
        "ERROR: [RECIPE METADATA (KB-H001)] The mandatory attribute 'homepage' is missing. Please, add it to the recipe.",
        "ERROR: [RECIPE METADATA (KB-H001)] The mandatory attribute 'topics' is missing. Please, add it to the recipe."
    ]

    def _get_environ(self, **kwargs):
        kwargs = super(TestKBH001, self)._get_environ(**kwargs)
        if not os.path.isdir(self.hooks_dir):
            os.makedirs(self.hooks_dir)
        if not os.path.isfile(os.path.join(self.hooks_dir, 'hook_conan_center.py')):
            hook_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hooks', 'hook_conan_center.py')
            shutil.copy2(hook_path, self.hooks_dir)
        return kwargs

    def test_basic_recipe(self):
        save(self, 'conanfile.py', content=self.conanfile_base.format(placeholder=''))
        output = self.conan(['export', '--version=0.1.0', 'conanfile.py'])
        for msg in self.bad_recipe_output:
            assert msg not in output
        assert "[RECIPE METADATA (KB-H001)] OK" in output

    def test_missing_attributes(self):
        save(self, 'conanfile.py', content=self.conanfile_empty.format(placeholder=''))
        output = self.conan(['export', '--name=package', '--version=0.1.0', '--user=acme', '--channel=testing', 'conanfile.py'])
        for msg in self.bad_recipe_output:
            assert msg in output
        assert "[RECIPE METADATA (KB-H001)] OK" not in output

    def test_author_attribute(self):
        save(self, 'conanfile.py', content=self.conanfile_base.format(placeholder='author = "John Doe"'))
        output = self.conan(['export', '--version=0.1.0', '--user=acme', '--channel=testing', 'conanfile.py'])
        assert "ERROR: [RECIPE METADATA (KB-H001)] Conanfile should not contain author attribute because all recipes are owned by the community. Please, remove it." in output

    def test_topics_attribute(self):
        save(self, 'conanfile.py', content=self.conanfile_base.format(placeholder='topics = ("conan",)'))
        output = self.conan(['export', '--version=0.1.0', '--user=acme', '--channel=testing', 'conanfile.py'])
        assert "WARN: [RECIPE METADATA (KB-H001)] The topic 'conan' is invalid and should be removed from topics attribute." in output

    def test_invalid_url(self):
        save(self, 'conanfile.py', content=self.conanfile_base.format(placeholder='url = "https://conan.io"'))
        output = self.conan(['export', '--version=0.1.0', '--user=acme', '--channel=testing', 'conanfile.py'])
        assert "ERROR: [RECIPE METADATA (KB-H001)] The attribute 'url' should point to: https://github.com/conan-io/conan-center-index" in output