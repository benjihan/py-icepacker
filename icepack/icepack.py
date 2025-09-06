# @file     icepack/icepack.py
# @author   Ben G. Han
# @date     2025-09-03
# @brief    Python interface for ice packer/depacker C library.

import os
import ctypes
import ctypes.util
from typing import Optional, Tuple
from importlib import resources
from sys import version_info
from platform import system as system_name

lib_base = 'unice68'
mod_name = 'icepack'

class IcepackError(Exception):
    """Custom exception for icepack module errors."""
    pass

def get_libformat() -> str:
    """
    Determine the platform-specific library file naming scheme by
    probing well known libraries.

    Returns:
        Format string e.g. ('lib%s.so') on Linux.

    Raises:
        IcepackError: If the library naming scheme cannot be determined.

    """
    pyver = 'python%d.%d'%(version_info.major,version_info.minor)
    for tpl in (pyver, 'expat', 'ssl',):
        try:
            path = ctypes.util.find_library(tpl)
            if not path: continue
            filename = os.path.basename(path)
            base, ext = os.path.splitext(filename)
            while ext[1:].isdigit():
                filename = base
                base, ext = os.path.splitext(filename)
            return filename.replace(tpl,'%s')
        except: pass

    # Reasonnable default for known systems
    system = system_name()
    if system in ( 'Linux', 'Android' ):
        pass
    elif system in ( 'Windows', ):
        return '%s.dll'
    elif system in ( 'Darwin', 'iOS' ):
        return 'lib%s.dylib'
    else:
        raise IcepackError("Could not determine library naming scheme")
    return 'lib%s.so'


def build_library_name(base_name: str) -> str:
    """
    Build the platform-specific library filename for a given base name.

    Args:
        base_name: The base name of the library (e.g., 'icepack').

    Returns:
        The platform-specific library filename (e.g., 'libicepack.so', 'icepack.dll').
    """
    return get_libformat() % base_name

class Icepack:
    """Python interface to the icepack C library."""

    def __init__(self, lib_path: Optional[str] = None):
        """
        Initialize the icepack library interface.

        Args:

            lib_path: Path to the icepack shared library. If None,
                      tries package-bundled binaries, local build, or
                      system library using find_library.

        Raises:
            IcepackError: If the library cannot be loaded.

        """
        if lib_path is None:
            # Try package-bundled precompiled library
            try:
                rsc_name = mod_name + ".lib"
                lib_name = build_library_name(lib_base)
                lib_path = None
                if resources.is_resource(rsc_name, lib_name):
                    with resources.path(rsc_name, lib_name) as x:
                        lib_path = str(x)
            except ImportError:
                pass

            # Try local build (e.g., from Makefile in build/)
            if lib_path is None:
                build_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                         mod_name)
                lib_name = build_library_name(lib_base)
                lib_path = os.path.join(build_dir, lib_name)
                if not os.path.exists(lib_path):
                    lib_path = None

            # Try system library using find_library
            if lib_path is None:
                lib_path = lib_path or ctypes.util.find_library(lib_base)
            if lib_path is None:
                raise IcepackError(f"Could not find {lib_base} library")

        try:
            self.lib = ctypes.cdll.LoadLibrary(lib_path)
        except OSError as e:
            raise IcepackError(f"Failed to load {lib_base} library from {lib_path}: {e}")

        # Configure function prototypes
        self._setup_functions()

    def _setup_functions(self):
        """Configure the C function prototypes and argument types."""
        # unice68_depacked_size
        self.lib.unice68_depacked_size.argtypes = [
            ctypes.c_void_p,  # const void * buffer
            ctypes.POINTER(ctypes.c_int)  # int * p_csize
        ]
        self.lib.unice68_depacked_size.restype = ctypes.c_int

        # unice68_depacker
        self.lib.unice68_depacker.argtypes = [
            ctypes.c_void_p,  # void * dst
            ctypes.c_void_p   # const void * src
        ]
        self.lib.unice68_depacker.restype = ctypes.c_int

        # unice68_packer
        self.lib.unice68_packer.argtypes = [
            ctypes.c_void_p,  # void * dst
            ctypes.c_int,     # int max
            ctypes.c_void_p,  # const void * src
            ctypes.c_int      # int len
        ]
        self.lib.unice68_packer.restype = ctypes.c_int

    def depacked_size(self, buffer: bytes) -> Tuple[int, int]:
        """
        Get the depacked size of a compressed buffer.

        Args:
            buffer: Input compressed data as bytes.

        Returns:
            Tuple of (depacked_size, compressed_size).

        Raises:
            IcepackError: If the function fails.
        """
        csize = ctypes.c_int()
        c_buffer = ctypes.c_void_p(ctypes.cast(buffer, ctypes.c_void_p).value)
        result = self.lib.unice68_depacked_size(c_buffer, ctypes.byref(csize))
        if result < 0:
            raise IcepackError(f"unice68_depacked_size failed with code {result}")
        return result, csize.value

    def depack(self, src: bytes) -> bytes:
        """
        Decompress data using the icepack library.

        Args:
            src: Input compressed data as bytes.

        Returns:
            Decompressed data as bytes.

        Raises:
            IcepackError: If decompression fails or input is invalid.
        """
        depacked_size, _ = self.depacked_size(src)
        if depacked_size <= 0:
            raise IcepackError("Invalid depacked size")

        dst = ctypes.create_string_buffer(depacked_size)
        c_src = ctypes.c_void_p(ctypes.cast(src, ctypes.c_void_p).value)
        result = self.lib.unice68_depacker(dst, c_src)
        if result != 0:
            raise IcepackError(f"unice68_depacker failed with code {result}")

        return dst.raw[:depacked_size]

    def pack(self, src: bytes, max_size: Optional[int] = None) -> bytes:
        """
        Compress data using the icepack library.

        Args:
            src: Input data to compress as bytes.
            max_size: Maximum size of the compressed output. If None, uses 12 + len(src) * 9 // 8.

        Returns:
            Compressed data as bytes.

        Raises:
            IcepackError: If compression fails, input is invalid, or buffer overflow occurs.
        """
        if not src:
            raise IcepackError("Input buffer cannot be empty")

        input_len = len(src)
        if max_size is None:
            max_size = 16 + ( input_len * 9 >> 3 )
        if max_size <= 0:
            raise IcepackError("Invalid maximum size")

        dst = ctypes.create_string_buffer(max_size)
        c_src = ctypes.c_void_p(ctypes.cast(src, ctypes.c_void_p).value)
        result = self.lib.unice68_packer(dst, max_size, c_src, input_len)
        if result < 0:
            raise IcepackError(f"unice68_packer failed with code {result}")
        elif result > max_size:
            raise IcepackError(f"unice68_packer overflowed by {result - max_size}")

        return dst.raw[:result]

if __name__ == "__main__":
    try:
        icepack = Icepack()
        test_data = b"Hello!"
        compressed = icepack.pack(test_data)
        print(f"Original size: {len(test_data)} bytes")
        print(f"Compressed size: {len(compressed)} bytes")
        depacked_size, compressed_size = icepack.depacked_size(compressed)
        print(f"Depacked size: {depacked_size}, Compressed size: {compressed_size}")
        decompressed = icepack.depack(compressed)
        print(f"Decompressed data: {decompressed.decode('utf-8')}")
    except IcepackError as e:
        print(f"Error: {e}")
