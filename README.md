# Conan Hooks

![logo](images/logo.png)

[![Build Status](https://ci.conan.io/job/Hooks/job/master/badge/icon)](https://ci.conan.io/job/Hooks/job/master/)

Repository to develop **experimental** [Conan](https://conan.io) hooks for Conan >= 1.8.

 * [Conan Center](#conan-center)
 * [Attribute checker](#attribute-checker)
 * [Binary linter](#binary-linter)
 * [Github updater](#github-updater)
 * [Member typo checker](#members-typo-checker)
 * [SPDX checker](#spdx-checker)
 * [Recipe linter](#recipe-linter)
 * [Non ASCII](#non-ascii)
 * [YAML linter](#yaml-linter)


## Hook setup

Place your hook Python files under *~/.conan/hooks*. The name of the hook would be the same one as the file name.

```
*~/.conan/hook/conan-center.py
```

Only copying hook files will not activate them.

## Conan config as installer

To install all hooks from Conan repository in Github:

``$ conan config install https://github.com/conan*io/hooks.git``

If you are using Conan >=1.14 you can specify the source and destination folder to avoid copying
undesired files to your local cache:

``$ conan config install https://github.com/conan-io/hooks.git -sf hooks -tf hooks ``

Conan config install does not activate any hook.

## Hook activation

You can activate any hook with:

``$ conan config set hooks.conan-center``

If you handle multiple dependencies in your project is better to add a *conan.conf*:

```
    [hooks]
    attribute_checker
    conan-center_reviewer
```

## Hooks

These are the hooks currently available in this repository

### [Conan Center](hooks/conan-center.py)

This hook does checks for the [inclusion guidelines of third-party libraries](https://docs.conan.io/en/latest/uploading_packages/artifactory/conan_center_guide.html)
in [Conan Center](https://conan.io/center/).

It is mostly intended for users who want to contribute packages to Conan Center. With this hook
they will test some of the requirements in the guidelines, as this hook will check for recipe
metadata, binary matching... during the ``conan create`` step and will output the result of each
check as ``OK``, ``WARNING`` or ``ERROR``:

```
[HOOK - conan-center_reviewer.py] pre_export(): [RECIPE METADATA] OK
[HOOK - conan-center_reviewer.py] pre_export(): [HEADER ONLY] OK
[HOOK - conan-center_reviewer.py] pre_export(): [NO COPY SOURCE] OK
[HOOK - conan-center_reviewer.py] pre_export(): [FPIC OPTION] OK
[HOOK - conan-center_reviewer.py] pre_export(): [FPIC MANAGEMENT] 'fPIC' option not found
[HOOK - conan-center_reviewer.py] pre_export(): [VERSION RANGES] OK
[HOOK - conan-center_reviewer.py] post_package(): ERROR: [PACKAGE LICENSE] No package licenses found in: ~/
.conan/data/name/version/jgsogo/test/package/3475bd55b91ae904ac96fde0f106a136ab951a5e. Please
 package the library license to a 'licenses' folder
[HOOK - conan-center_reviewer.py] post_package(): [DEFAULT PACKAGE LAYOUT] OK
[HOOK - conan-center_reviewer.py] post_package(): [MATCHING CONFIGURATION] OK
[HOOK - conan-center_reviewer.py] post_package(): [SHARED ARTIFACTS] OK
```

If you want the hook to fail the execution, if an error is reported, you can adjust the environment
variable ``CONAN_HOOK_ERROR_LEVEL``:
   - ``CONAN_HOOK_ERROR_LEVEL=40`` it will raise if any error happen.
   - ``CONAN_HOOK_ERROR_LEVEL=30`` it will raise if any error or warning happen.



### [Attribute checker](hooks/attribute_checker.py)

This hook checks that some important attributes are present in the ``ConanFile``: url,
license and description, and will output a warning for the missing ones.

### [Binary Linter](hooks/binary_linter.py)

This Conan hook validates produced binary artifacts of the given package.

Binaries stored in the package folder are checked for compatibility with package settings and options.

Currently, the following checks are performed:

- Binary format (Mach-O, ELF or PE)
- Architecture
- No shared libraries are produced for *shared=False*
- Visual Studio runtime library in use

The hook uses [LIEF](https://github.com/lief-project/LIEF) library in order to perform its checks.

The hook is automatically called when *package* command is executed.

### [GitHub Updater](hooks/github_updater.py)

This Conan hook reads your recipe and updates its GitHub repository properties using the attributes.

The following attributes are updated:

- homepage

- description

- topics

It's necessary to pass GitHub token by environment variable: *GITHUB_TOKEN*.

### [Members Typo checker](hooks/members_typo_checker.py)

This `pre_export()` hook checks `ConanFile`'s members for potential typos, for example:

```py
from conans import ConanFile

class ConanRecipe(ConanFile):
    name = "name"
    version = "version"

    export_sources = "OH_NO"
```

Will produce the next warning:

```bash
pre_export(): WARN: The 'export_sources' member looks like a typo. Similar to:
pre_export(): WARN:     exports_sources
```

### [SPDX checker](hooks/spdx_checker.py)

This Conan hook validates that conanfile's [license](https://docs.conan.io/en/latest/reference/conanfile/attributes.html?highlight=license#license) attribute specifies valid license identifier(s) from the [SPDX license list](https://spdx.org/licenses/).

The hook uses [spdx_lookup](https://pypi.org/project/spdx-lookup/) python module in order to perform its checks.

Use `pip install spdx_lookup` in order to install required dependency.

The hook is automatically called when *export* command is executed.

### [Recipe linter](hooks/recipe_linter.py)

This hook runs [Pylint](https://www.pylint.org/) over the recipes before exporting
them (it runs in the `pre_export` hook), it can be really useful to check for
typos, code flaws or company standards.

There several environment variables you can use to configure it:
 * `CONAN_PYLINTRC`: path to a configuration file to fully customize Pylint behavior.
 * `CONAN_PYLINT_WERR`: if set, linting errors will trigger a `ConanException`.
 * `CONAN_PYLINT_RECIPE_PLUGINS`: list of modules (comma separated list) to load. They are used to register additional checker or dynamic fields before running
 the linter. By default it points to the `conans.pylint_plugin` module distributed
 together with Conan, this file contains the declaration of some extra fields that are valid in the `ConanFile` class.

This hook requires additional dependencies to work: `pip install pylint astroid`.

### [Non ASCII](hooks/non_ascii.py)

Separate KB-H047 from Conan Center, which is no longer required due Python 2.7 deprecation.

Validates if `conanfile.py` and `test_package/conanfile.py` contain a non-ascii present, when there is a character, it logs an error.

### [YAML linter](hooks/yaml_linter.py)

This hook runs [yamllint](https://yamllint.readthedocs.io/) over the yaml files
in a recipe before exporting them (it runs in the `pre_export` hook), it can be
really useful to check for typos.

This hook requires additional dependencies to work: `pip install yamllint`.

## License

[MIT License](LICENSE)
