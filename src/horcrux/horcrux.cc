#include <string>

#include <spawn.h>

#include <lldb/API/LLDB.h>

namespace horcrux {

class LoadCmd : public lldb::SBCommandPluginInterface {
  public:
   LoadCmd() {}
   ~LoadCmd() override {}

   bool DoExecute(lldb::SBDebugger d, char** cmd,
                  lldb::SBCommandReturnObject& result) override {
     lldb::SBListener listener{};
     lldb::SBError error;
     const char *argv[] = {
       "/Users/mmarchini/workspace/nodejs/node/out/Release/phoenix",
       nullptr
     };
     const char *envp[] = { nullptr };

     lldb::SBTarget host_target = d.CreateTarget("/Users/mmarchini/workspace/nodejs/node/out/Release/phoenix");
     lldb::SBProcess host_process = host_target.Launch(listener, reinterpret_cast<const char**>(argv), reinterpret_cast<const char**>(envp), nullptr, nullptr, nullptr, nullptr, 0, true, error);

     lldb::SBTarget core_target = d.CreateTarget(*cmd);
     lldb::SBProcess core_process = core_target.LoadCore(*cmd);


     d.SetSelectedTarget(host_target);

     if (error.Fail()) {
       result.Printf("Error while launching host process: ");
       result.SetError(error);
       return false;
     }

     int regions_len = 0;
     int failed_regions = 0;

     lldb::SBMemoryRegionInfoList memory_regions = core_process.GetMemoryRegions();
     lldb::SBMemoryRegionInfo region_info;

     for (uint32_t i = 0; i < memory_regions.GetSize(); ++i) {
       memory_regions.GetMemoryRegionAtIndex(i, region_info);

       // Skip executable pages (what about JIT pages?)
       if (region_info.IsExecutable()) {
         continue;
       }

       regions_len++;

       uint64_t address = region_info.GetRegionBase();
       uint64_t len = region_info.GetRegionEnd() - region_info.GetRegionBase();

       char* block = new char[len];

       core_process.ReadMemory(address, block, len, error);
       if (error.Fail()) {
         result.Printf("Error while reading from core dump: ");
         result.SetError(error);
         return false;
       }

       lldb::SBError write_error;
       host_process.WriteMemory(address, block, len, write_error);
       if (write_error.Fail()) {
         failed_regions++;
       }

       delete[] block;
     }

     result.Printf("%d regions (%d failed)\n", regions_len, failed_regions);

     return true;
   }
};

class StackCmd : public lldb::SBCommandPluginInterface {
  public:
   StackCmd() {}
   ~StackCmd() override {}

   bool DoExecute(lldb::SBDebugger d, char** cmd,
                  lldb::SBCommandReturnObject& result) override {
     return true;
   }
};


} // namespace horcrux

namespace lldb {

bool PluginInitialize(SBDebugger d) {
  SBCommandInterpreter interpreter = d.GetCommandInterpreter();

  SBCommand v8 = interpreter.AddMultiwordCommand("v8", "V8 helpers");

  v8.AddCommand("load", new horcrux::LoadCmd());
  v8.AddCommand("stack", new horcrux::StackCmd());

  return true;
}

}  // namespace lldb
