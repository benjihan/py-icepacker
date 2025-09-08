# @file     icepacker/icepacker.py
# @author   Ben G. Han
# @date     2025-09-03
# @brief    Python interface for ice packer/depacker C library.

from os import path as ospath
import ctypes
from ctypes.util import find_library
from typing import Optional, Tuple
from importlib import resources
from importlib.util import find_spec
from sys import version_info
from platform import system as system_name

lib_base = 'unice68'
mod_name = 'icepacker'

class IcepackerError(Exception):
    """Custom exception for icepack module errors."""
    pass

def get_libformat() -> str:
    """
    Determine the platform-specific library file naming scheme by
    probing well known libraries.

    Returns:
        Format string e.g. ('lib%s.so') on Linux.

    Raises:
        IcepackerError: If the library naming scheme cannot be determined.

    """
    pyver = 'python%d.%d'%(version_info.major,version_info.minor)
    for tpl in (pyver, 'expat', 'ssl',):
        try:
            path = find_library(tpl)
            if not path: continue
            filename = ospath.basename(path)
            base, ext = ospath.splitext(filename)
            while ext[1:].isdigit():
                filename = base
                base, ext = ospath.splitext(filename)
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
        raise IcepackerError("Could not determine library naming scheme")
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

class Icepacker:
    """Python interface to the icepack C library."""

    def __init__(self, lib_path: Optional[str] = None):
        """
        Initialize the icepack library interface.

        Args:

            lib_path: Path to the icepack shared library. If None,
                      tries package-bundled binaries, local build, or
                      system library using find_library.

        Raises:
            IcepackerError: If the library cannot be loaded.

        """
        self.lib = None

        if lib_path is None:

            # Expected library filename for this platform.
            lib_name = build_library_name(lib_base)

            # Try buddy/bunddle library first [icepacker/lib/{lib_name}].
            if resources.is_resource(mod_name, "lib", lib_name):
                with resources.path(mod_name,"lib",lib_name) as x:
                    if self._setup_functions(str(x)):
                        return

            # Try setup build [unice68/lib/{libname}]
            top_dir = ospath.dirname(ospath.dirname(__file__))

            # [icepacker/lib/libunice68.so]
            if self._setup_functions(ospath.join(top_dir,lib_path)):
                return

            # Check for source dir unice68
            if ospath.isfile(ospath.join(top_dir,lib_base,"unice68.h")):
                lib_path = ospath.join(mod_name, "lib", lib_name)

                # [build/lib/icepacker/lib/libunice68.so]
                if self._setup_functions(ospath.join(top_dir,"build","lib",lib_path)):
                    return

                # [unice68/libunice68.so]
                if self._setup_functions(ospath.join(top_dir, lib_base, lib_name)):
                    return

            # Finally: System library
            if self._setup_functions(find_library(lib_base)):
                return

            raise IcepackerError(f"Could not find a suitable {lib_base} library")

    def _setup_functions(self, lib_path: Optional[str] = None) -> bool:
        """Configure the C function prototypes and argument types."""

        try:
            if lib_path:
                self.lib = ctypes.cdll.LoadLibrary(lib_path)

            # unice68_depacked_size
            self.lib.unice68_depacked_size.argtypes = [
                ctypes.c_void_p,             # const void * buffer
                ctypes.POINTER(ctypes.c_int) # int * p_csize
            ]
            self.lib.unice68_depacked_size.restype = ctypes.c_int

            # unice68_depacker
            self.lib.unice68_depacker.argtypes = [
                ctypes.c_void_p, # void * dst
                ctypes.c_void_p  # const void * src
            ]
            self.lib.unice68_depacker.restype = ctypes.c_int

            # unice68_packer
            self.lib.unice68_packer.argtypes = [
                ctypes.c_void_p, # void * dst
                ctypes.c_int,    # int max
                ctypes.c_void_p, # const void * src
                ctypes.c_int     # int len
            ]
            self.lib.unice68_packer.restype = ctypes.c_int

        except (OSError, AttributeError) as E:
            self.lib = None

        return self.lib is not None

    def depacked_size(self, buffer: bytes) -> Tuple[int, int]:
        """
        Get the depacked size of a compressed buffer.

        Args:
            buffer: Input compressed data as bytes.

        Returns:
            Tuple of (depacked_size, compressed_size).

        Raises:
            IcepackerError: If the function fails.
        """
        csize = ctypes.c_int()
        c_buffer = ctypes.c_void_p(ctypes.cast(buffer, ctypes.c_void_p).value)
        result = self.lib.unice68_depacked_size(c_buffer, ctypes.byref(csize))
        if result < 0:
            raise IcepackerError(f"unice68_depacked_size failed with code {result}")
        return result, csize.value

    def depack(self, src: bytes) -> bytes:
        """
        Decompress data using the icepack library.

        Args:
            src: Input compressed data as bytes.

        Returns:
            Decompressed data as bytes.

        Raises:
            IcepackerError: If decompression fails or input is invalid.
        """
        depacked_size, packed_size = self.depacked_size(src)
        if depacked_size <= 0:
            raise IcepackerError("Invalid depacked size")
        if packed_size > len(src):
            raise IcepackerError(f"Missing packed data")

        dst = ctypes.create_string_buffer(depacked_size)
        c_src = ctypes.c_void_p(ctypes.cast(src, ctypes.c_void_p).value)
        result = self.lib.unice68_depacker(dst, c_src)
        if result != 0:
            raise IcepackerError(f"unice68_depacker failed with code {result}")

        return dst.raw[:depacked_size]

    def pack(self, src: bytes, max_size: Optional[int] = None) -> bytes:
        """
        Compress data using Ice! packer.

        Args:
            src: Input data to compress as bytes.
            max_size: Maximum size of the compressed output.

        Returns:
            Compressed data as bytes.

        Raises:
            IcepackerError
        """
        if not src:
            raise IcepackerError("Input buffer cannot be empty")
        input_len = len(src)

        if not max_size: max_size = 16 + ( input_len * 9 >> 3 )
        if max_size <= 0:
            raise IcepackerError("Invalid maximum size")

        dst = ctypes.create_string_buffer(max_size)
        c_src = ctypes.c_void_p(ctypes.cast(src, ctypes.c_void_p).value)
        result = self.lib.unice68_packer(dst, max_size, c_src, input_len)
        if result < 0:
            raise IcepackerError(f"unice68_packer failed [{result}]")
        elif result > max_size:
            raise IcepackerError(f"unice68_packer overflowed by {result - max_size}")

        return dst.raw[:result]

if __name__ == "__main__":
    try:
        ice = Icepacker()
        test_data = b"Hello!"
        compressed = ice.pack(test_data)
        print(f"Original size: {len(test_data)} bytes")
        print(f"Compressed size: {len(compressed)} bytes")
        depacked_size, compressed_size = ice.depacked_size(compressed)
        print(f"Depacked size: {depacked_size}, Compressed size: {compressed_size}")
        decompressed = ice.depack(compressed)
        print(f"Decompressed data: {decompressed.decode('utf-8')}")
    except IcepackerError as e:
        print(f"Error: {e}")
