import os
import textwrap
import platform

from conans import tools

from tests.utils.test_cases.conan_client import ConanClientTestCase


class RecipeFolderSizeTests(ConanClientTestCase):
    conanfile = textwrap.dedent("""\
        from conans import ConanFile

        class AConan(ConanFile):
            url = "fake_url.com"
            license = "fake_license"
            description = "whatever"
        """)

    def _get_environ(self, **kwargs):
        kwargs = super(RecipeFolderSizeTests, self)._get_environ(**kwargs)
        kwargs.update({'CONAN_HOOKS': os.path.join(os.path.dirname(__file__), '..', '..', '..',
                                                   'hooks', 'conan-center')})
        return kwargs

    def test_regular_folder_size(self):
        content = "".join(["k" for it in range(1024 * 255)])
        tools.save('conanfile.py', content=self.conanfile)
        tools.save('big_file', content=content)
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("[RECIPE FOLDER SIZE] OK", output)
        self.assertNotIn("ERROR: [RECIPE FOLDER SIZE]", output)

    def test_larger_folder_size(self):
        content = "".join(["k" for it in range(1024 * 257)])
        tools.save('conanfile.py', content=self.conanfile)
        tools.save('big_file', content=content)
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("ERROR: [RECIPE FOLDER SIZE] The size of your recipe folder", output)

    def test_custom_folder_size(self):
        tools.save('conanfile.py', content=self.conanfile)
        content = " ".join(["test_recipe_folder_larger_size" for it in range(500)])
        tools.save('big_file', content=content)
        output = self.conan(['export', '.', 'name/version@user/channel'])
        self.assertIn("[RECIPE FOLDER SIZE] OK", output)
        with tools.environment_append({"CONAN_MAX_RECIPE_FOLDER_SIZE_KB": "0"}):
            output = self.conan(['export', '.', 'name/version@user/channel'])
            self.assertIn("ERROR: [RECIPE FOLDER SIZE] The size of your recipe folder", output)
