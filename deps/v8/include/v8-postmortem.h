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
   * Returns true if this value is an object.
   */
  bool IsObject();

 private:
  int GetInstanceType();
  int HasHeapObjectTag();
  int GetOddballKind();
  uintptr_t address_;
  MemoryAccessor* memory_accessor_;
};


};
};
