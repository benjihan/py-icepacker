# icepacker - Unice68 Python Interface

A Python interface for the `unice68` C library, enabling data
compression and decompression using the `unice68_depacked_size`,
`unice68_depacker`, and `unice68_packer` functions.

## Installation

```bash
pip install .
```

### Prerequisites

The build process will look for a suitable unice68 library in the
`icepacker/lib` directory. If it does not found one it will try to
compile one using the Makefile. If this failed it will check for a
system-wide version.

- **For compilation**:
  - A C compiler (`gcc`, `clang` on Linux/macOS, `MSVC` or `MinGW` on Windows).
  - `make` (included in most Unix environments, or via `MinGW` on Windows).
  

### Customizing Compilation Flags

To customize compilation flags, set environment variables before
running `pip install`:

 | Variables | Default value |
 | :-------- | :------------ |
 | `CC`      | `cc`          | 
 | `CFLAGS`  | Guessed `-O2 -shared -DNDEBUG=1` |
 | `LIBNAME` | Guessed `libunice68.so`,`libunice68.dylib`,`unice68.dll` |

```bash
export CC=x86_64-w64-mingw32-gcc
export CFLAGS="-O3 -march=native"
export LIBNAME=unice68.dll # Just for example, it should be guessed properly
pip install .
```

### Usage

```python
from icepacker import Icepacker

ice = Icepacker()
data = b"Hello!"
compressed = ice.pack(data)
decompressed = ice.depack(compressed)
print(decompressed.decode('utf-8'))
```

### Manual Compilation (Optional)

If you prefer to compile `libunice68` manually:

```bash
mkdir -p icepacker/lib
make -C icepacker/lib -f unice68/Makefile CC=gcc LIBNAME=libunice68.so
```
### Security issue

The `icepacker.pack()` function calls `unice68_pack()` C function that
is not properly protected against buffer overflow. Chance for it to
happen are quiet low as the python module allocate supplemental memory
to mitigate the situation. It will be fixed in a near future.
