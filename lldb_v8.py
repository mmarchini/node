#!/usr/bin/python

import re
import lldb
import commands
import argparse

launch_args = [
  None,
  None,
  None,
  None,
  None,
  None,
  0,
  True,
]

HOST = "/Users/mmarchini/workspace/nodejs/node/out/Release/phoenix"


def v8_load(debugger, args, result, internal_dict):
  error = lldb.SBError()

  host_target = debugger.CreateTarget(HOST)
  host_process = host_target.Launch(debugger.GetListener(), *(launch_args + [error]))
  debugger.SetSelectedTarget(host_target)

  if error.Fail():
    result.SetError(error)
    return False

  #  core_target = debugger.CreateTarget(args.core_path)
  #  core_process = core_target.LoadCore(args.core_path)

  #  if error.Fail():
    #  result.SetError(error)
    #  return False

  #  memory_ranges = core_process.GetMemoryRegions()
  #  memory_info = lldb.SBMemoryRegionInfo()

  #  regions = 0
  #  failures = 0

  #  for i in range(memory_ranges.GetSize()):
    #  if not memory_ranges.GetMemoryRegionAtIndex(i, memory_info):
      #  print >>result, "Range unavailable:", i

    #  if not memory_info.IsWritable():
      #  continue

    #  regions += 1

    #  addr = memory_info.GetRegionBase()
    #  range_len = memory_info.GetRegionEnd() - addr

    #  content = core_process.ReadMemory(addr, range_len, error)
    #  if error.Fail():
      #  result.SetError(error)
      #  return False

    #  write_error = lldb.SBError()
    #  written = host_process.WriteMemory(addr, content, write_error)
    #  if write_error.Fail() or written != range_len:
      #  failures += 1

      #  byte_count = 0
      #  byte_failures = 0
      #  # Falls back to slow method
      #  for j in range(range_len):
        #  byte_count += 1
        #  written = host_process.WriteMemory(addr, str(content[j]), write_error)
        #  if write_error.Fail() or written != range_len:
          #  byte_failures += 1

      #  print >>result, "Region #%d in slow mode: %d bytes (%d failed)" % (i, byte_count, byte_failures)

  #  print >>result, "%d Regions (%d Failed)" % (regions, failures)

  #  core_process.Destroy()
  #  debugger.DeleteTarget(core_target)

  print "a"
  breakpoint = host_target.BreakpointCreateByName("HandleDebuggerRequest")
  if not breakpoint.IsValid() or breakpoint.num_locations == 0 or not breakpoint.IsEnabled():
    print "error trying to set breakpoint"
    return False
  print "b"
  host_process.Continue()
  print "c"

  return True


def communicate_with_process(process, message):
  process.PutSTDIN("%s\n" % message)
  process.Continue()
  return process.GetSTDOUT(1000).strip("\n")


def v8_stack(debugger, args, result, internal_dict):
  target = debugger.GetSelectedTarget()
  process = target.GetProcess()

  print >>result, communicate_with_host(process, "s")
  return True


def v8_print(debugger, args, result, internal_dict):
  target = debugger.GetSelectedTarget()
  process = target.GetProcess()

  print >>result, communicate_with_host(process, "p")
  return True


HEX_RE = re.compile(r"^(?:0x){0,1}[0-9a-f]+")
def validate_hex(val):
  match = HEX_RE.match(val)
  if not match:
      raise argparse.ArgumentTypeError
  return int(val, 16)


def v8_handler(debugger, command, result, internal_dict):
  v8_parser = argparse.ArgumentParser(prog='v8', description='v8-related commands')
  subparsers = v8_parser.add_subparsers()

  load_parser = subparsers.add_parser('load')
  load_parser.add_argument("core_path", type=str)
  load_parser.set_defaults(func=v8_load)

  stack_parser = subparsers.add_parser('stack')
  stack_parser.set_defaults(func=v8_stack)

  print_parser = subparsers.add_parser('print')
  print_parser.add_argument("address", type=validate_hex)
  print_parser.set_defaults(func=v8_print)

  args = v8_parser.parse_args(command.split(" "))
  args.func(debugger, args, result, internal_dict)

  return True


# And the initialization code to add your commands
def __lldb_init_module(debugger, internal_dict):
  debugger.HandleCommand('command script add -f lldb_v8.v8_handler v8')
