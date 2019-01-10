# coding=utf-8
from checks.recipe_metadata import recipe_metadata_check  # keep imports relative


def pre_export(output, conanfile, *args, **kwargs):
    recipe_metadata_check(conanfile, output)
