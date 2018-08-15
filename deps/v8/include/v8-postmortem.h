#ifndef _V8_POSTMORTEM_H
#define _V8_POSTMORTEM_H
#include "v8.h"

namespace v8 {

namespace postmortem {

class MemoryAccessor {
 public:
  virtual uintptr_t ReadMemory(uintptr_t address, size_t size);
};

class Value {
 public:
  Value(uintptr_t address, MemoryAccessor* memory_accessor) :
      address_(address), memory_accessor_(memory_accessor) {}

  inline uintptr_t address() { return address_; }

  /**
   * Returns true if this value is the undefined value.  See ECMA-262
   * 4.3.10.
   */
  bool IsUndefined();

  /**
   * Returns true if this value is the null value.  See ECMA-262
   * 4.3.11.
   */
  bool IsNull();

  /**
   * Returns true if this value is either the null or the undefined value.
   * See ECMA-262
   * 4.3.11. and 4.3.12
   */
  bool IsNullOrUndefined();

  /**
   * Returns true if this value is an object.
   */
  bool IsObject();

  /**
   * Returns true if this value is a 32-bit signed integer.
   */
  bool IsInt32();

  /**
   * Returns true if this value is a 32-bit unsigned integer.
   */
  bool IsUint32();

 private:
  int GetInstanceType();
  int HasHeapObjectTag();
  int GetOddballKind();
  uintptr_t address_;
  MemoryAccessor* memory_accessor_;
};


};
};

#endif
