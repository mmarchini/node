#ifndef _V8_POSTMORTEM_H
#define _V8_POSTMORTEM_H
#include "v8.h"

namespace v8 {

namespace postmortem {

class MemoryAccessor {
 public:
  virtual uintptr_t ReadMemory(uintptr_t address, size_t size);

  template <class C>
  C Get(uintptr_t address) {
    return C(address, this);
  }
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

 protected:
  int GetInstanceType();
  int HasHeapObjectTag();
  int GetOddballKind();

 private:
  uintptr_t address_;
  MemoryAccessor* memory_accessor_;
};

#define POSTMORTEM_CONSTRUCTOR(Class, Parent)   \
    Class(uintptr_t address, MemoryAccessor* memory_accessor) : \
      Parent(address, memory_accessor) {}

/**
 * The superclass of primitive values.  See ECMA-262 4.3.2.
 */
class Primitive : public Value {
 public:
  POSTMORTEM_CONSTRUCTOR(Primitive, Value)
};

/**
 * A JavaScript number value (ECMA-262, 4.3.20)
 */
class Number : public Primitive {
 public:
  POSTMORTEM_CONSTRUCTOR(Number, Primitive)
  double Value();
};

/**
 * A JavaScript value representing a signed integer.
 */
class Integer : public Number {
 public:
  POSTMORTEM_CONSTRUCTOR(Integer, Number)
  int64_t Value();
};

/**
 * A JavaScript value representing a 32-bit signed integer.
 */
class Int32 : public Integer {
 public:
  POSTMORTEM_CONSTRUCTOR(Int32, Integer)

  int32_t Value();
};


/**
 * A JavaScript value representing a 32-bit unsigned integer.
 */
class Uint32 : public Integer {
 public:
  POSTMORTEM_CONSTRUCTOR(Uint32, Integer)

  uint32_t Value();
};

/**
 * A superclass for symbols and strings.
 */
class V8_EXPORT Name : public Primitive {
 public:
  POSTMORTEM_CONSTRUCTOR(Name, Primitive)
  /**
   * Returns the identity hash for this object. The current implementation
   * uses an inline property on the object to store the identity hash.
   *
   * The return value will never be 0. Also, it is not guaranteed to be
   * unique.
   */
  int GetIdentityHash();
};

/**
 * A JavaScript string value (ECMA-262, 4.3.17).
 */
class V8_EXPORT String : public Name {
  POSTMORTEM_CONSTRUCTOR(String, Name)

  /**
   * Returns the number of characters (UTF-16 code units) in this string.
   */
  int Length();

  /**
   * Returns whether this string is known to contain only one byte data,
   * i.e. ISO-8859-1 code points.
   * Does not read the string.
   * False negatives are possible.
   */
  bool IsOneByte();

#if 0
  /**
   * Returns the number of bytes in the UTF-8 encoded
   * representation of this string.
   */
  int Utf8Length();

  /**
   * Returns whether this string contain only one byte data,
   * i.e. ISO-8859-1 code points.
   * Will read the entire string in some cases.
   */
  bool ContainsOnlyOneByte();

  /**
   * Returns true if the string is external
   */
  bool IsExternal();

  /**
   * Returns true if the string is both external and one-byte.
   */
  bool IsExternalOneByte();

  /**
   * Returns the C++ string representation
   */
  std::string ToCString();
#endif
};

};
};

#endif
