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

Conan config install does not activate any hook.

## Hook activation

You can activate any hook with:

``$ conan config set hooks.conan-center``

If you handle multiple dependencies in your project is better to add a *conan.conf*:

```
    [hooks]
    attribute_checker
    conan-center
```

## Hooks

These are the hooks currently available in this repository

### [Attribute checker](hooks/attribute_checker.py)

This hook checks that some important attributes are present in the ``ConanFile``: url,
license and description, and will output a warning for the missing ones.

### [Bintray Update](hooks/bintray_update.py)

This Conan hook reads your recipe and updates its Bintray package info using the attributes.

It's necessary pass Bintray login by environment variables:
  - CONAN_LOGIN_USERNAME: Bintray login username
  - CONAN_PASSWORD: Bintray API KEY

The hook is automatically called when upload command is executed.

### [Binary Linter](hooks/binary-linter.py)

This Conan hook validates produced binary artifacts of the given package.

Binaries stored in the package folder are checked for compatibility with package settings and options.

Currently, the following checks are performed:

- Binary format (Mach-O, ELF or PE)
- Architecture
- No shared libraries are produced for *shared=False*
- Visual Studio runtime library in use

The hook uses [LIEF](https://github.com/lief-project/LIEF) library in order to perform its checks.

The hook is automatically called when *package* command is executed.

## License

[MIT License](LICENSE)
