# coding=utf-8


def pre_export(output, conanfile, *args, **kwargs):
    if not 'os' in conanfile.settings:
        return
    if not 'os_build' in conanfile.settings:
        return

    output.warn("This package defines both 'os' and 'os_build'")
    output.warn("Please use 'os' for libraries and 'os_build'")
    output.warn("only for build-requires used for cross-building")
