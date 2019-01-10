
def recipe_metadata_check(conanfile, output):
    """
    Checks for recipe attributes 'url', 'license' and 'description'
    :param conanfile: Conanfile object
    :param output:  Output object
    :return: True if check was successful, False otherwise
    """
    test_name = "[RECIPE METADATA]"
    result_check = True
    if not getattr(conanfile, 'alias', None):
        for field in ["url", "license", "description"]:
            field_value = getattr(conanfile, field, None)
            if not field_value:
                result_check = False
                output.error("%s Conanfile doesn't have '%s'. It is recommended to add it as "
                             "attribute" % (test_name, field))
    if result_check:
        output.success("%s OK" % test_name)
    return result_check
