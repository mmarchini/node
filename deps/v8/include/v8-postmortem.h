#ifndef _V8_POSTMORTEM_H
#define _V8_POSTMORTEM_H

namespace v8 {

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
 private:
  static bool is_enabled_;
  static PostmortemAnalyzer* current_;
};
};

#endif
