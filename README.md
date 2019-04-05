[![Build Status](https://travis-ci.org/conan-io/hooks.svg?branch=master)](https://travis-ci.org/conan-io/hooks)
[![Build status](https://ci.appveyor.com/api/projects/status/s0k4n197ko1iyoml/branch/master?svg=true)](https://ci.appveyor.com/project/ConanCIintegration/hooks/branch/master)


# Conan Hooks

Repository to develop **experimental** [Conan](https://conan.io) hooks for Conan >= 1.8.

**WARNING**: Hooks were originally named "Plugins"

## Hook setup

Place your hook Python files under *~/.conan/hooks*. The name of the hook would be the same one as the file name.

```
*~/.conan/hook/conan-center.py
```

Only copying hook files will not activate them.

## Conan config as installer

To install all hooks from Conan repository in Github:

``$ conan config install https://github.com/conan-io/hooks``

If you are using Conan >=1.14 you can specify the source and destination folder to avoid copying
undesired files to your local cache:

``$ conan config install https://github.com/conan-io/hooks -sf hooks -tf hooks ``

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

### [Conan Center reviewer](hooks/conan-center_reviewer.py)

This hook does checks for the [inclusion guidelines of third-party libraries](https://docs.conan.io/en/latest/uploading_packages/bintray/conan_center_guide.html#inclusion-guidelines-for-third-party-libraries)
in [Conan Center](https://bintray.com/conan/conan-center).

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

### [Attribute checker](hooks/attribute_checker.py)

This hook checks that some important attributes are present in the ``ConanFile``: url,
license and description, and will output a warning for the missing ones.

### [Bintray Updater](hooks/bintray_updater.py)

This Conan hook reads your recipe and updates its Bintray package info using the attributes.

It's necessary pass Bintray login by environment variables:
  - BINTRAY_LOGIN_USERNAME: Bintray login username
  - BINTRAY_PASSWORD: Bintray API KEY

The hook is automatically called when upload command is executed.

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

### [SPDX checker](hooks/spdx_checker.py)

This Conan hook validates that conanfile's [license](https://docs.conan.io/en/latest/reference/conanfile/attributes.html?highlight=license#license) attribute specifies valid license identifier(s) from the [SPDX license list](https://spdx.org/licenses/).

The hook uses [spdx_lookup](https://pypi.org/project/spdx-lookup/) python module in order to perform its checks.

Use `pip install spdx_lookup` in order to install required dependency.

The hook is automatically called when *export* command is executed.

## License

[MIT License](LICENSE)
