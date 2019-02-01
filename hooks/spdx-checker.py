# -*- coding: utf-8 -*-

import spdx_lookup


def check_license(output, license_id):
    if spdx_lookup.by_id(license_id):
        output.info('license "%s" is a valid SPDX license identifier' % license_id)
    else:
        output.error('license "%s" is not a valid SPDX license identifier' % license_id)


def pre_export(output, conanfile, conanfile_path, reference, **kwargs):
    del conanfile_path, reference, kwargs

    if "license" not in conanfile.__dict__:
        output.info("recipe doesn't have a license attribute")
        return
    if isinstance(conanfile.license, str):
        licenses = [conanfile.license]
    elif isinstance(conanfile.license, tuple):
        licenses = conanfile.license
    else:
        output.error("don't know how to process license attribute which is neither string nor tuple")
        return
    for license_id in licenses:
        check_license(output, license_id)
