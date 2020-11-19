import inspect
from difflib import get_close_matches

from conans import ConanFile


def pre_export(output, conanfile, conanfile_path, reference, **kwargs):
    def get_base_members(conanfile):
        return [m[0] for m in inspect.getmembers(conanfile) if not m[0].startswith('_')]

    base_members = get_base_members(ConanFile)
    base_members.extend(["requires", "build_requires", "requirements",
                         "build_requirements", "python_requires", "python_requires_extend",
                         "keep_imports", "imports", "build_id", "deploy", "scm"])

    def get_members(conanfile):
        # We use a different function on the conanfile because members
        # `user` and `channel` throw an Exception on access when they're empty
        return [m for m in dir(conanfile) if not m.startswith('_')]

    for member in get_members(conanfile):
        if member in base_members:
            continue

        matches = get_close_matches(
            word=member, possibilities=base_members, n=5, cutoff=0.80)
        if len(matches) == 0:
            continue

        output.warn("The '%s' member looks like a typo. Similar to:" % member)
        for match in matches:
            output.warn("    %s" % match)
