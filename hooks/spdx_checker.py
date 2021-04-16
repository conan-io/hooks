# -*- coding: utf-8 -*-

import spdx_lookup


def check_license(output, license_id):
    license_value = spdx_lookup.by_id(license_id)
    # use case-sensitive check
    if license_value and license_value.id == license_id:
        output.info('license "%s" is a valid SPDX license identifier' % license_id)
    else:
        output.error('license "%s" is not a valid SPDX license identifier' % license_id)


def pre_export(output, conanfile, conanfile_path, reference, **kwargs):
    del conanfile_path, reference, kwargs

    if getattr(conanfile, "license", None) is None:
        output.info("recipe doesn't have a license attribute")
        return
    if isinstance(conanfile.license, str):
        licenses = [conanfile.license]
    elif isinstance(conanfile.license, (tuple, list)):
        licenses = conanfile.license
    else:
        output.error("don't know how to process license attribute which is neither string nor tuple")
        return
    for license_id in licenses:
        check_license(output, license_id)
