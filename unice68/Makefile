#! /usr/bin/make -f
#
# @file    src/Makefile
# @author  Ben "G" Han
# @brief   Simple Makefile to build unice8 as a shared library.
#

vpath %.c $(dir $(lastword $(MAKEFILE_LIST)))

# Default compiler and flags
CC = cc
CFLAGS = -O2 -fPIC -shared
STRIP = strip -s
ifeq (gcc,$(CC:%gcc=gcc))
  STRIP = $(CC:%gcc=%strip) -s
endif

# Platform-specific settings
ifeq ($(OS),Windows_NT)
  LIBNAME = unice68.dll
  CC = cl
  CFLAGS = /O2 /LD
else
  ifneq (,$(findstring mingw,$(basename $(CC))))
    LIBNAME = unice68.dll
  else
    UNAME_S := $(shell uname -s)
    ifeq ($(UNAME_S),Linux)
      LIBNAME = libunice68.so
    else ifeq ($(UNAME_S),Darwin)
      LIBNAME = libunice68.dylib
    else
      LIBNAME = libunice68.so
    endif
  endif
endif

# Source files
SOURCES = unice68_pack.c unice68_unpack.c

all-strip: all strip

all: $(LIBNAME)

strip: $(LIBNAME)
	$(STRIP) $(LIBNAME)

$(LIBNAME): $(SOURCES)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^

clean:;	rm -f -- $(LIBNAME)

.PHONY: all-strip all strip clean
