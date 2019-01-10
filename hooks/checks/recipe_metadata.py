
def recipe_metadata_check(conanfile, output, output_name=False, output_level=None):
    """
    Checks for recipe attributes 'url', 'license' and 'description'
    :param conanfile: Conanfile object
    :param output:  Output object
    :return: True if check was successful, False otherwise
    """
    test_name = "[RECIPE METADATA] " if output_name else ""
    message = output.warn if not output_level else output_level
    result_check = True
    if not getattr(conanfile, 'alias', None):
        for field in ["url", "license", "description"]:
            field_value = getattr(conanfile, field, None)
            if not field_value:
                result_check = False
                message("%sConanfile doesn't have '%s'. It is recommended to add it as attribute"
                        % (test_name, field))
    if result_check and test_name:
        output.success("%sOK" % test_name)
    return result_check
