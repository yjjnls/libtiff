#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, CMake, tools
import os
import shutil
from conanos.build import config_scheme

try:
    import conanos.conan.hacks.cmake
except:
    if os.environ.get('EMSCRIPTEN_VERSIONS'):
        raise Exception(
            'Please use pip install conanos to patch conan for emscripten binding !')
class LibtiffConan(ConanFile):
    name = "libtiff"
    description = "Library for Tag Image File Format (TIFF)"
    version = "4.0.9"
    url = "http://github.com/bincrafters/conan-tiff"
    author = "Bincrafters <bincrafters@gmail.com>"
    license = "MIT"
    homepage = "http://www.simplesystems.org/libtiff"
    exports = ["LICENSE.md"]
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = 'shared=False', 'fPIC=True'
    requires = "zlib/1.2.11@conanos/stable"

    _source_subfolder = "source_subfolder"

    def is_emscripten(self):
        try:
            return self.settings.compiler == 'emcc'
        except:
            return False

    def config_options(self):
        if self.settings.os == "Windows":
            self.options.remove("fPIC")

    def configure(self):
        del self.settings.compiler.libcxx

        if self.is_emscripten():
            del self.settings.os
            del self.settings.arch
            self.options.remove("fPIC")
            self.options.remove("shared")

    def source(self):
        tools.get("http://download.osgeo.org/libtiff/tiff-{0}.zip".format(self.version))
        os.rename('tiff-' + self.version, self._source_subfolder)
        os.rename(os.path.join(self._source_subfolder, "CMakeLists.txt"),
                  os.path.join(self._source_subfolder, "CMakeListsOriginal.txt"))
        shutil.copy("CMakeLists.txt",
                    os.path.join(self._source_subfolder, "CMakeLists.txt"))

    def build(self):
        cmake = CMake(self)

        cmake.definitions['CMAKE_INSTALL_LIBDIR'] = 'lib'
        cmake.definitions['CMAKE_INSTALL_BINDIR'] = 'bin'
        cmake.definitions['CMAKE_INSTALL_INCLUDEDIR'] = 'include'

        cmake.definitions["lzma"] = False
        cmake.definitions["jpeg"] = False
        if not self.is_emscripten() and self.options.shared and self.settings.compiler == "Visual Studio":
            # https://github.com/Microsoft/vcpkg/blob/master/ports/tiff/fix-cxx-shared-libs.patch
            tools.replace_in_file(os.path.join(self._source_subfolder, 'libtiff', 'CMakeLists.txt'),
                                  r'set_target_properties(tiffxx PROPERTIES SOVERSION ${SO_COMPATVERSION})',
                                  r'set_target_properties(tiffxx PROPERTIES SOVERSION ${SO_COMPATVERSION} '
                                  r'WINDOWS_EXPORT_ALL_SYMBOLS ON)')

        if not self.is_emscripten() and self.settings.os == "Windows" and self.settings.compiler != "Visual Studio" and self.version == '4.0.8':
            # only one occurence must be patched. fixed in 4.0.9
            tools.replace_in_file(os.path.join(self._source_subfolder, "CMakeListsOriginal.txt"),
                                  "if (UNIX)",
                                  "if (UNIX OR MINGW)")

        if self.is_emscripten():
            cmake.definitions['STATIC'] = False

        cmake.definitions["BUILD_SHARED_LIBS"] = True if self.is_emscripten() else self.options.shared
        cmake.configure(source_folder=self._source_subfolder)
        cmake.build()
        cmake.install()

    def package(self):
        self.copy("COPYRIGHT", src=self._source_subfolder, dst="licenses", ignore_case=True, keep_path=False)
        shutil.rmtree(os.path.join(self.package_folder, 'share', 'man'), ignore_errors=True)
        shutil.rmtree(os.path.join(self.package_folder, 'share', 'doc'), ignore_errors=True)

        # remove binaries
        for bin_program in ['fax2ps', 'fax2tiff', 'pal2rgb', 'ppm2tiff', 'raw2tiff', 'tiff2bw', 'tiff2pdf',
                            'tiff2ps', 'tiff2rgba', 'tiffcmp', 'tiffcp', 'tiffcrop', 'tiffdither', 'tiffdump',
                            'tiffgt', 'tiffinfo', 'tiffmedian', 'tiffset', 'tiffsplit']:
            for ext in ['', '.exe']:
                try:
                    os.remove(os.path.join(self.package_folder, 'bin', bin_program+ext))
                except:
                    pass

    def package_info(self):
        self.cpp_info.libs = ["tiff", "tiffxx"]
        if not self.is_emscripten() and self.settings.os == "Windows" and self.settings.build_type == "Debug" and self.settings.compiler == 'Visual Studio':
            self.cpp_info.libs = [lib+'d' for lib in self.cpp_info.libs]
        if not self.is_emscripten() and self.options.shared and self.settings.os == "Windows" and self.settings.compiler != 'Visual Studio':
            self.cpp_info.libs = [lib+'.dll' for lib in self.cpp_info.libs]
        if not self.is_emscripten() and self.settings.os == "Linux":
            self.cpp_info.libs.append("m")
