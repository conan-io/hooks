#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import os
import lief


class BinaryLinter(object):
    def __init__(self, output, conanfile, conanfile_path):
        self._output = output
        self._conanfile = conanfile
        self._conanfile_path = conanfile_path
        self._output.info('conan binary linter plug-in')

        self._os = self._conanfile.settings.get_safe('os') or self._conanfile.settings.get_safe('os_build')
        self._subsystem = self._conanfile.settings.get_safe('os.subsystem')
        self._version = self._conanfile.settings.get_safe('os.version')
        self._api_level = self._conanfile.settings.get_safe('os.api_level')
        self._arch = self._conanfile.settings.get_safe('arch') or self._conanfile.settings.get_safe('arch_build')
        self._compiler = self._conanfile.settings.get_safe('compiler')
        self._build_type = self._conanfile.settings.get_safe('build_type')
        self._compiler_version = self._conanfile.settings.get_safe('compiler.version')
        self._compiler_runtime = self._conanfile.settings.get_safe('compiler.runtime')
        self._compiler_libcxx = self._conanfile.settings.get_safe('compiler.libcxx')
        self._shared = self._conanfile.options.get_safe("shared")
        self._fPIC = self._conanfile.options.get_safe("fPIC")

        self._expected_format = {
            'Windows': lief.EXE_FORMATS.PE,
            'WindowsStore': lief.EXE_FORMATS.PE,
            'Linux': lief.EXE_FORMATS.ELF,
            'Android': lief.EXE_FORMATS.ELF,
            'FreeBSD': lief.EXE_FORMATS.ELF,
            'SunOS': lief.EXE_FORMATS.ELF,
            'Macos': lief.EXE_FORMATS.MACHO,
            'iOS': lief.EXE_FORMATS.MACHO,
            'watchOS': lief.EXE_FORMATS.MACHO,
            'tvOS': lief.EXE_FORMATS.MACHO
        }.get(self._os, None)

    def verify(self):
        if not self._expected_format:
            self._output.warn("don't know how to verify for os %s, giving up..." % self._os)
            return
        for root, _, filenames in os.walk(self._conanfile.package_folder):
            for filename in filenames:
                filename = os.path.join(root, filename)
                self._verify_file(filename)

    def _verify_file(self, filename):
        self._filename = filename
        self._binary = lief.parse(filename)

        if not self._binary:
            return

        if self._binary.format != self._expected_format:
            self._output.error('"%s" invalid executable format %s, expected %s'
                               % (self._filename, self._binary.format, self._expected_format))
            return

        self._binary = self._binary.concrete
        self._output.info('checking file "%s"' % filename)

        {
            lief.EXE_FORMATS.ELF: self._verify_elf,
            lief.EXE_FORMATS.PE: self._verify_pe,
            lief.EXE_FORMATS.MACHO: self._verify_macho
        }.get(self._binary.format)()

        if self._shared is not None and not self._shared:
            if self._is_shared_library:
                self._output.error('"%s" is shared library, but option "shared" is set to "False"' % self._filename)

    @property
    def _is_shared_library(self):
        if self._binary.format == lief.EXE_FORMATS.ELF:
            return self._binary.header.file_type == lief.ELF.E_TYPE.DYNAMIC
        elif self._binary.format == lief.EXE_FORMATS.PE:
            return self._binary.header.has_characteristic(lief.PE.HEADER_CHARACTERISTICS.DLL)
        elif self._binary.format == lief.EXE_FORMATS.MACHO:
            return self._binary.header.file_type == lief.MachO.FILE_TYPES.DYLIB
        return False

    def _verify_elf(self):
        expected_machine_type = {'x86': lief.ELF.ARCH.i386,
                                 'x86_64': lief.ELF.ARCH.x86_64,
                                 'armv6': lief.ELF.ARCH.ARM,
                                 'armv7': lief.ELF.ARCH.ARM,
                                 'armv7s': lief.ELF.ARCH.ARM,
                                 'armv7k': lief.ELF.ARCH.ARM,
                                 'armv7hf': lief.ELF.ARCH.ARM,
                                 'armv8': lief.ELF.ARCH.AARCH64,
                                 'avr': lief.ELF.ARCH.AVR,
                                 'ppc': lief.ELF.ARCH.PPC,
                                 'ppcle': lief.ELF.ARCH.PPC,
                                 'ppc64': lief.ELF.ARCH.PPC64,
                                 'ppc64le': lief.ELF.ARCH.PPC64,
                                 'sparc': lief.ELF.ARCH.SPARC,
                                 'sparcv9': lief.ELF.ARCH.SPARCV9,
                                 'mips': lief.ELF.ARCH.MIPS,
                                 'mips64': lief.ELF.ARCH.MIPS}.get(self._arch, None)

        if self._binary.header.machine_type != expected_machine_type:
            self._output.error('"%s" invalid machine type %s, expected %s'
                               % (self._filename, expected_machine_type, self._binary.header.machine_type))

    def _verify_pe(self):
        expected_machine_type = {'x86': lief.PE.MACHINE_TYPES.I386,
                                 'x86_64': lief.PE.MACHINE_TYPES.AMD64,
                                 'armv6': lief.PE.MACHINE_TYPES.ARM,
                                 'armv7': lief.PE.MACHINE_TYPES.ARM,
                                 'armv7s': lief.PE.MACHINE_TYPES.ARM,
                                 'armv7k': lief.PE.MACHINE_TYPES.ARM,
                                 'armv7hf': lief.PE.MACHINE_TYPES.ARM,
                                 'armv8': lief.PE.MACHINE_TYPES.ARM}.get(self._arch, None)  # FIXME : ARM64

        if self._binary.header.machine != expected_machine_type:
            self._output.error('"%s" invalid machine type %s, expected %s'
                               % (self._filename, expected_machine_type, self._binary.header.machine))

        if self._compiler == 'Visual Studio':
            self._verify_runtime()
        self._check_import("cygwin1.dll", self._subsystem == "cygwin")
        self._check_import("msys-1.0.dll", self._subsystem == "msys")
        self._check_import("msys-2.0.dll", self._subsystem == "msys2")

    def _has_import(self, name):
        for i in self._binary.imports:
            if i.name.lower() == name:
                return True
        return False

    def _check_import(self, library, expected):
        if self._has_import(library):
            if not expected:
                self._output.warn('"%s" imports library "%s"' % (self._filename, library))
            else:
                self._output.info('"%s" imports library "%s"' % (self._filename, library))
        elif not self._has_import(library):
            if expected:
                self._output.error('"%s" doesn\'t import library "%s"' % (self._filename, library))
            else:
                self._output.info('"%s" doesn\'t import library "%s"' % (self._filename, library))

    @property
    def _runtime_libraries(self):
        def runtime_name(version):
            return 'msvcr%s0' % version if version < 14 else 'vcruntime140'

        return {str(version): {'MDd': runtime_name(version) + 'd.dll',
                               'MD': runtime_name(version) + '.dll'} for version in range(8, 16)}

    def _verify_runtime(self):
        for version in self._runtime_libraries:
            for runtime in self._runtime_libraries[version]:
                library = self._runtime_libraries[version][runtime]
                compiler_version = str(self._compiler_version)
                expected = self._runtime_libraries[compiler_version].get(self._compiler_runtime)
                expected = library == expected
                expected = expected and "MT" not in self._compiler_runtime
                self._check_import(library, expected)

    def _verify_macho(self):
        expected_machine_type = {'x86': lief.MachO.CPU_TYPES.x86_64,
                                 'x86_64': lief.MachO.CPU_TYPES.x86_64,
                                 'ppc': lief.MachO.CPU_TYPES.POWERPC,
                                 'ppcle': lief.MachO.CPU_TYPES.POWERPC,
                                 'ppc64': lief.MachO.CPU_TYPES.POWERPC64,
                                 'ppc64le': lief.MachO.CPU_TYPES.POWERPC64,
                                 'armv6': lief.MachO.CPU_TYPES.ARM,
                                 'armv7': lief.MachO.CPU_TYPES.ARM,
                                 'armv7s': lief.MachO.CPU_TYPES.ARM,
                                 'armv7k': lief.MachO.CPU_TYPES.ARM,
                                 'armv7hf': lief.MachO.CPU_TYPES.ARM,
                                 'armv8': lief.MachO.CPU_TYPES.ARM}.get(self._arch, None)
        if self._binary.header.cpu_type != expected_machine_type:
            self._output.error('"%s" invalid machine type %s, expected %s'
                               % (self._filename, expected_machine_type, self._binary.header.machine))


def post_package(output, conanfile, conanfile_path, **kwargs):
    binary_linter = BinaryLinter(output, conanfile, conanfile_path)
    binary_linter.verify()
