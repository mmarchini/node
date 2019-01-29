#include <string>
#include <iostream>
#include <fstream>      // std::fstream
#include <stdlib.h>     /* rand */

#include <v8-postmortem-debugger.h>

void HandleDebuggerRequest() {

}

int main(int argc, char* argv[]) {
  std::ifstream stdin(argv[1]);
  std::ofstream stdout(argv[2]);

  std::cout << argv[1] << std::endl;
  std::cout << argv[2] << std::endl;

  std::string buffer;

  while (true) {
    getline(stdin, buffer);
    if (stdin.eof()) {
      stdin.clear();
      stdin.sync();
      // stdin.seekg(0, std::ios::beg);
      if (buffer.empty()) continue;
    }
    std::cout << "f" << std::endl;
    std::cout << "      i" << std::endl;
    std::cout << "      i" << std::endl;
    std::cout << "      i" << std::endl;
    std::cout << "      i" << std::endl;
    std::cout << "      i" << std::endl;
    std::cout << "      i" << std::endl;
    std::cout << "      i" << std::endl;

    switch (buffer.c_str()[0]) {
      case 's':
        // V8PostmortemPrintStackTrace(command->stack_pointer, command->program_counter,
                                    // &GetRegister, &GetTlsData, &GetStaticData);
        stdout << "Print stack" << std::endl;
        break;
      case 'p':
        stdout << "Print object" << std::endl;
        break;
      default:
        std::cerr << "Invalid option '" << buffer.c_str()[0] << "'" << std::endl;
    }
  }
  return 0;
}
