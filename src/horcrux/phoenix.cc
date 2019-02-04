#include <string>
#include <iostream>
#include <fstream>      // std::fstream
#include <stdlib.h>     /* rand */
#include <unistd.h>
#include <cstring>

#include <fcntl.h>
#include <sys/mman.h>

#include <v8-postmortem-debugger.h>

#define LOGGER(M) std::cout << "[phoenix] " << M << std::endl

static std::ifstream input;
static std::ofstream output;

// TODO (mmarchini): V8 should provide a way to determine the register name
#define GENERAL_REGISTERS(V) \
  V(rax)                     \
  V(rcx)                     \
  V(rdx)                     \
  V(rbx)                     \
  V(rsp)                     \
  V(rbp)                     \
  V(rsi)                     \
  V(rdi)                     \
  V(r8)                      \
  V(r9)                      \
  V(r10)                     \
  V(r11)                     \
  V(r12)                     \
  V(r13)                     \
  V(r14)                     \
  V(r15)

enum RegisterCode {
#define REGISTER_CODE(R) kRegCode_##R,
  GENERAL_REGISTERS(REGISTER_CODE)
#undef REGISTER_CODE
      kRegAfterLast
};

void LoadMemoryAddresses() {
  std::string buffer;

  while (true) {
    getline(input, buffer);
    if (input.eof()) {
      input.clear();
      input.sync();
      if (buffer.empty()) continue;
    }

    std::cerr << buffer << std::endl;
    if (buffer == "done") break;

    char fromBuffer[buffer.length() + 1] = { 0 };
    buffer.copy(fromBuffer, buffer.length());
    unsigned long long addr = std::stoul(strtok(fromBuffer, " "), nullptr, 16);
    size_t len = std::stoul(strtok(nullptr, " "));
    char* filePath = strtok(nullptr, " ");

    // TODO (mmarchini) change mmap with something cross-platform
    std::cerr << filePath << std::endl;
    int fd = open(filePath, O_RDWR);

    if (fd == -1) {
      std::cerr << "error while opening file '" << filePath << "': " << strerror(errno) << std::endl;
      output << "-1" << std::endl;
      continue;
    }

    void* result = mmap(reinterpret_cast<void*>(addr), static_cast<size_t>(len),
                        PROT_READ | PROT_WRITE | PROT_EXEC, MAP_FIXED | MAP_SHARED, fd, 0);

    if (result == MAP_FAILED) {
      std::cerr << "map failed " << strerror(errno) << std::endl;
      output << "-1" << std::endl;
    } else if (result != reinterpret_cast<void*>(addr)) {
      std::cerr << "allocated in incorrect address 0x" << std::hex << result << std::dec << std::endl;
      output << "-1" << std::endl;
    } else {
      output << len << std::endl;
    }

    // TODO(mmarchini): Check if we can close the fd when a file is mapped to memory
    close(fd);
  }
}


uintptr_t GetRegister(int index) {
  switch (index) {
#define REGISTER_CODE(R)                           \
    case kRegCode_##R:                             \
      output << "GetRegister " << #R << std::endl; \
      break;
  GENERAL_REGISTERS(REGISTER_CODE)
#undef REGISTER_CODE
    default:
      std::cerr << "Couldn't determine register for index " << index << std::endl;
      return 0;
  }

  std::string buffer;
  while (true) {
    getline(input, buffer);
    if (input.eof()) {
      input.clear();
      input.sync();
      if (buffer.empty()) continue;
    }
    return std::stoul(buffer);
  }
}


void* GetTlsData(int32_t key) {
  output << "GetTlsData " << key << std::endl;
  LOGGER("Loading tls data");

  std::string buffer;
  while (true) {
    getline(input, buffer);
    if (input.eof()) {
      input.clear();
      input.sync();
      if (buffer.empty()) continue;
    }

    LOGGER("here ya go");
    LOGGER(buffer);

    unsigned long long value = std::stoul(buffer, nullptr, 16);

    LOGGER("result: " << std::hex << value << std::dec);
    return reinterpret_cast<void*>(value);
  }
}

StaticAccessResult GetStaticData(const char* name, uint8_t* destination,
                                 size_t byte_count) {
  // TODO (mmarchini) maybe convert to Base64 to avoid special characters
  // issues? Is that even possible (the issues)?
  output << "GetStaticData " << byte_count << " " << name << std::endl;
  LOGGER("Loading " << name);

  std::string buffer;
  while (true) {
    getline(input, buffer);
    if (input.eof()) {
      input.clear();
      input.sync();
      if (buffer.empty()) continue;
    }

    // Well, we're ignoring byte_count, so just get the first byte
    LOGGER(name << "["<< byte_count << "]: ");
    for (unsigned int i = 0; i < byte_count; i++) {
      destination[i] = buffer.c_str()[i];
      LOGGER( "    " << std::hex << unsigned(destination[i]) << std::dec);
    }

    return StaticAccessResult::kOk;
  }
  return StaticAccessResult::kOk;
}


int main(int argc, char* argv[]) {
  input = std::ifstream(argv[1]);
  output = std::ofstream(argv[2]);

  std::cerr << argv[1] << std::endl;
  std::cerr << argv[2] << std::endl;

  std::string buffer;

  LoadMemoryAddresses();

  while (true) {
    getline(input, buffer);
    if (input.eof()) {
      input.clear();
      input.sync();
      if (buffer.empty()) continue;
    }

    switch (buffer.c_str()[0]) {
      case 's': {
        std::cerr << "one" << std::endl;
        char fromBuffer[buffer.length() + 1] = { 0 };
        buffer.copy(fromBuffer, buffer.length());
        strtok(fromBuffer, " ");
        uintptr_t stack_pointer = std::stoul(strtok(nullptr, " "));
        uintptr_t program_counter = std::stoul(strtok(nullptr, " "));
        V8PostmortemPrintStackTrace(stack_pointer, program_counter,
                                    &GetRegister, &GetTlsData, &GetStaticData);

        output << "end" << std::endl;
        break;
      }
      case 'p':
        output << "Print object" << std::endl;
        break;
      default:
        std::cerr << "Invalid option '" << buffer.c_str()[0] << "'" << std::endl;
        break;
    }
  }

  return 0;
}
