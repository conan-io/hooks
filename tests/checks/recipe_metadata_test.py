import unittest

from checks.recipe_metadata import recipe_metadata_check
from tests.utils.conanfile import MockConanfile
from tests.utils.output import MockOutput


class WrongConanfileRecipeMetadataTest(unittest.TestCase):

    def setUp(self):
        self.output = MockOutput()
        self.conanfile = None

    def test(self):
        recipe_metadata_check(self.conanfile, self.output, output_name=True,
                              output_level=self.output.error)
        self.assertIn("ERROR: [RECIPE METADATA] Conanfile doesn't have 'url'. It is recommended to "
                      "add it as attribute", self.output)
        self.assertIn("ERROR: [RECIPE METADATA] Conanfile doesn't have 'license'. It is recommended"
                      " to add it as attribute", self.output)
        self.assertIn("ERROR: [RECIPE METADATA] Conanfile doesn't have 'description'. It is "
                      "recommended to add it as attribute", self.output)


class ConanfileRecipeMetadataTest(unittest.TestCase):

    def setUp(self):
        self.conanfile = MockConanfile(None)
        self.output = self.conanfile.output

    def no_metadata_test(self):
        recipe_metadata_check(self.conanfile, self.output, output_name=True,
                              output_level=self.output.error)
        self.assertIn("ERROR: [RECIPE METADATA] Conanfile doesn't have 'url'. It is recommended to "
                      "add it as attribute", self.output)
        self.assertIn("ERROR: [RECIPE METADATA] Conanfile doesn't have 'license'. It is recommended"
                      " to add it as attribute", self.output)
        self.assertIn("ERROR: [RECIPE METADATA] Conanfile doesn't have 'description'. It is "
                      "recommended to add it as attribute", self.output)

    def all_metadata_test(self):
        self.conanfile.url = "url"
        self.conanfile.license = "license"
        self.conanfile.description = "description"
        recipe_metadata_check(self.conanfile, self.output, output_name=True,
                              output_level=self.output.error)
        self.assertNotIn("ERROR: [RECIPE METADATA] Conanfile doesn't have 'url'. It is recommended "
                         "to add it as attribute", self.output)
        self.assertNotIn("ERROR: [RECIPE METADATA] Conanfile doesn't have 'license'. It is "
                         "recommended to add it as attribute", self.output)
        self.assertNotIn("ERROR: [RECIPE METADATA] Conanfile doesn't have 'description'. It is "
                         "recommended to add it as attribute", self.output)
        self.assertIn("[RECIPE METADATA] OK", self.output)

    def no_url_empty_description_test(self):
        self.conanfile.license = "license"
        self.conanfile.description = ""

        recipe_metadata_check(self.conanfile, self.output, output_name=True,
                              output_level=self.output.error)

        self.assertIn("ERROR: [RECIPE METADATA] Conanfile doesn't have 'url'. It is recommended to "
                      "add it as attribute", self.output)
        self.assertNotIn("ERROR: [RECIPE METADATA] Conanfile doesn't have 'license'. It is "
                         "recommended to add it as attribute", self.output)
        self.assertIn("ERROR: [RECIPE METADATA] Conanfile doesn't have 'description'. It is "
                      "recommended to add it as attribute", self.output)

    def alias_test(self):
        self.conanfile.alias = True
        recipe_metadata_check(self.conanfile, self.output, output_name=True,
                              output_level=self.output.error)
        self.assertIn("[RECIPE METADATA] OK", self.output)
