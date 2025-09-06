# @file     setup.py
# @author   Ben G. Han
# @date     2025-09-03
# @brief    Python interface for ice packer/depacker C library.

import os
import platform
import sys
import subprocess
from setuptools import setup, find_packages
from setuptools.command.build_py import build_py
from ctypes import cdll
from ctypes.util import find_library

modname='icepack'
libbase='unice68'
top_dir = os.path.dirname(__file__)
lib_dir = os.path.join(top_dir, modname, 'lib')

class CustomBuildPy(build_py):
    """Custom build command to compile unice68 using a simple Makefile."""

    def run(self):
        lib_name = self.get_library_name()
        lib_path = os.path.join(lib_dir, lib_name)

        if not os.path.exists(lib_path):
            # If the library file does not exists, try to build it
            self.build_nativelib()

        if not self.check_library(lib_path):
            # Could not load the compiled (or precompiled), try to
            # find it elsewhere.
            lib_path = find_library(libbase)
            if not lib_path or not self.check_library(lib_path):
                raise RuntimeError(f"unable to load a suitable '{libbase}' library")

        # Run standard build_py command
        super().run()

    def check_library(self, lib_path: str) -> bool:
        """Try to load existing shared library."""
        try:
            lib = cdll.LoadLibrary(lib_path)
            print(f"Check loaded DLL: {lib_path}")
            for symbol in ('unice68_packer','unice68_depacker','unice68_depacked_size'):
                if not hasattr(lib, symbol):
                    raise RuntimeError(f'{symbol} symbol not found in {lib_path}')
                print(f"- found {symbol}()")
        except OSError as e:
            return False
        return True

    def get_library_name(self) -> str:
        """Determine the platform-specific library filename."""

        # Defined in evironment variable ?
        libname = os.getenv('LIBNAME')
        if libname:
            # sanity check: libbase should be somewhere in there.
            if libbase in libname: return libname
            raise RuntimeError(f"LIBNAME={libname} does not contain '{libbase}'")

        # Windows ?
        if hasattr(sys, 'winver'): return libbase + '.dll'

        # Try to deduce the name from other well known libraries
        pyver = 'python%d.%d'%(sys.version_info.major,sys.version_info.minor)
        for tpl in ( pyver, 'expat', 'ssl', ):
            try:
                path = find_library(tpl)
                if not path: continue
                filename = os.path.basename(path)
                # Remove versioning
                base, ext = os.path.splitext(filename)
                while ext[1:].isdigit():
                    filename = base
                    base, ext = os.path.splitext(filename)
                return filename.replace(tpl, libbase)
            except: pass

        # Reasonable default for known systems
        system = platform.system()
        if system in ( 'Windows', ):
            return libbase + '.dll'
        elif system in ( 'Darwin', 'iOS' ):
            return 'lib'+libbase+'.dylib'
        elif system not in ( 'Linux', 'Android' ):
            print('Warning: could not determine platform dynamic library naming scheme')
        return 'lib'+libbase+'.so'

    def build_nativelib(self):
        """Compile unice68 using Makefile."""
        src_dir = os.path.join(top_dir, "unice68")
        lib_dir = os.path.join(top_dir, modname, 'lib')
        os.makedirs(lib_dir, exist_ok=True)

        print(f"Building {libbase}:")
        print(f"- src_dir: {src_dir}")
        print(f"- lib_dir: {lib_dir}")
        try:
            # Run make
            makefile = os.path.join(src_dir,"Makefile")
            make_cmd = ["make", "-Bf", makefile, "-C", lib_dir]
            for var in ( "CC","CFLAGS","LIBNAME" ):
                val = os.getenv(var)
                if val is not None:
                    print(f"- Add '{var}={val}'")
                    make_cmd.append(var+'='+val)
            subprocess.check_call(make_cmd)
            print(f"Sucessfully build {libbase}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Building {libbase} failed: {e}")
            return False

setup(
    # Minimal setup.py as metadata is in pyproject.toml
    packages=find_packages(),
    package_data={
        "icepack": [
            f"lib/lib{libbase}.so",
            f"lib/{libbase}.dll",
            f"lib/lib{libbase}.dylib",
        ]
    },
    cmdclass={"build_py": CustomBuildPy},
)
