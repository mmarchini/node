// Copyright 2018 the V8 project authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

// Functionality in this file is exposed for use by a crash dump debug helper
// ("postmortem host"). The process using this functionality should have mapped
// all of the memory from the dump file into its own memory at the same
// addresses, so it can use V8's object printing routines as if it were a live
// debugging session. For a more complete description of the responsibilities of
// the postmortem host, see the design document at
// https://docs.google.com/document/d/1aYHJoWROM5U5ULhCzwBfRPuMpSLnLg9Zt0fKEuGgUZQ/edit?usp=sharing

#ifndef V8_INCLUDE_V8_POSTMORTEM_DEBUGGER_H_
#define V8_INCLUDE_V8_POSTMORTEM_DEBUGGER_H_

#include <stdint.h>
#include <fstream>
#include <iostream>

#include "v8config.h"  // NOLINT(build/include)

extern "C" {

enum class StaticAccessResult {
  kOk,
  kSymbolNotFound,
  kMemoryNotAccessible,
  kBufferTooSmall,
  kGenericError,
};

// Functionality that must be provided by the postmortem host:

// Gets a register from the debuggee by register index.
typedef uintptr_t (*RegisterAccessFunction)(int index);

// Gets a piece of data from thread local storage by index.
typedef void* (*ThreadLocalAccessFunction)(int32_t key);

// Accesses a global or a static member of a class, using symbolic lookup in the
// debuggee process. Name must be fully qualified. Writes no more than
// byte_count bytes into the destination.
typedef StaticAccessResult (*StaticAccessFunction)(const char* name,
                                                   uint8_t* destination,
                                                   size_t byte_count);

// Functionality exposed by this module:

// Prints details about an object. The object should be a tagged pointer.
V8_EXPORT void V8PostmortemPrintObject(void* object, RegisterAccessFunction r,
                                       ThreadLocalAccessFunction t,
                                       StaticAccessFunction s,
                                       std::ostream& output=std::cout);

// Prints the current JS call stack.
V8_EXPORT void V8PostmortemPrintStackTrace(uintptr_t stack_pointer,
                                           uintptr_t program_counter,
                                           RegisterAccessFunction r,
                                           ThreadLocalAccessFunction t,
                                           StaticAccessFunction s,
                                           FILE* output=stdout);
}

#endif
