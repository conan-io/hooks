# coding=utf-8
from hooks.checks.recipe_metadata import recipe_metadata_check


def pre_export(output, conanfile, *args, **kwargs):
    recipe_metadata_check(conanfile, output)
