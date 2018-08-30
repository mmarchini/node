#ifndef _V8_POSTMORTEM_H
#define _V8_POSTMORTEM_H
// #include "include/v8.h"

namespace v8 {

class Isolate;
class Value;

#define POSTMORTEM_MODE V8_UNLIKELY(::v8::PostmortemAnalyzer::is_enabled())

namespace internal {
// class HeapIterator;
class ObjectIterator;
}; // namespace internal

class PostmortemAnalyzer {
 public:
  template<typename C>
  C ReadObject(const uintptr_t address) {
    uintptr_t ptr = this->ReadPointer(address);
    return *reinterpret_cast<C*>(&ptr);
  }

  virtual uintptr_t ReadPointer(const uintptr_t address);

  void Enable();
  void Disable();

  template <typename C>
  C Get(uintptr_t address) {
    return reinterpret_cast<C>(address);
  }

  static PostmortemAnalyzer* GetCurrent() {
    return PostmortemAnalyzer::current_;
  }

  static bool is_enabled() {
    return PostmortemAnalyzer::is_enabled_;
  }

  static void SetCurrentIsolate(Isolate* isolate);

  class HeapIterator {
   public:
    explicit HeapIterator(Isolate* isolate);

    ~HeapIterator();

    Value* next();
   private:
    std::unique_ptr<internal::ObjectIterator> heap_iterator_;
  };

 private:
  static bool is_enabled_;
  static PostmortemAnalyzer* current_;

  friend class Isolate;
};
};

struct PostmortemTips {
  v8::Isolate* current_isolate = nullptr;
};

#endif
