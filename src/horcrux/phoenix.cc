#include <string>
#include <iostream>

#include <v8-postmortem-debugger.h>



void HandleDebuggerRequest() {
  std::string buffer;
  getline(std::cin, buffer);

  switch (buffer.c_str()[0]) {
    case 's':
      // V8PostmortemPrintStackTrace(command->stack_pointer, command->program_counter,
                                  // &GetRegister, &GetTlsData, &GetStaticData);
      std::cout << "Print stack" << std::endl;
      break;
    case 'p':
      std::cout << "Print object" << std::endl;
      break;
    default:
      std::cerr << "Invalid option" << std::endl;
  }
}

int main() {
  while (true) {
    HandleDebuggerRequest();
  }
  return 0;
}
