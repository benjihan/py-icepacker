# Unice68 Python Interface

A Python interface for the `unice68` C library, enabling data compression and decompression using the `unice68_depacked_size`, `unice68_depacker`, and `unice68_packer` functions.

## Installation

```bash
pip install .
```

The package includes prebuilt binaries for Linux x86_64 (`libunice68.so`), Windows 64-bit (`unice68.dll`), and macOS (`libunice68.dylib`) in `icepack/lib/`. If no binary is available for your platform, `libunice6i8` will be compiled from source using a simple `Makefile`.

### Prerequisites

- **For prebuilt binaries**: No prerequisites.
- **For compilation**:
  - A C compiler (`gcc`, `clang` on Linux/macOS, `MSVC` or `MinGW` on Windows).
  - `make` (included in most Unix environments, or via `MinGW` on Windows).

### Customizing Compilation Flags

To customize compilation flags, set environment variables before running `pip install`:

 | Variables | Default value |
 | :-------- | :------------ |
 | `CC`      | `cc`          | 
 | `CFLAGS`  | Guessed `-O2 -shared -DNDEBUG=1` |
 | `LIBNAME` | Guessed `libunice68.so`,`libunice68.dylib`,`unice68.dll` |

```bash
export CC=x86_64-w64-mingw32-gcc
export CFLAGS="-O3 -march=native -L/path/to/libs"
export LIBNAME=unice68.dll # Just for example, it should be guessed properly
pip install .
```

### Usage

```python
from icepack import Icepack

icepack = Icepack()
data = b"Hello!"
compressed = icepack.pack(data)
decompressed = icepack.depack(compressed)
print(decompressed.decode('utf-8'))
```

### Manual Compilation (Optional)

If you prefer to compile `libunice68` manually:

```bash
cd src
make
cp -- *unice68*.{dll,so,dylib} ../icepack/lib/
```

On Windows with MSVC:

```bash
cd src
cl.exe /LD icepack.c /Fe../icepack/lib/icepack.dll
```

### Notes for Windows

- If using MSVC, compile manually with `cl.exe` as shown above.
- With MinGW, automatic compilation works with `make`.
- Prebuilt binaries in `icepack/lib/` are used automatically if available.

### Troubleshooting

If you encounter the error "Could not find icepack library", check that:
- A prebuilt binary is present in `icepack/lib/` (e.g., `libunice68.so`, `unice68.dll`).
- A system library is installed and accessible via `LD_LIBRARY_PATH` (Linux), `PATH` (Windows), or equivalent.
- You have compiled `libunice68` manually and placed the result in `icepack/lib/` with the appropriate name (e.g., `libunice68.so` on Linux).
