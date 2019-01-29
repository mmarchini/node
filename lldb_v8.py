#!/usr/bin/python

import os
from os import path
from time import sleep
import re
import lldb
import commands
import argparse
import tempfile
from pprint import pprint
from collections import OrderedDict

HOST = "/Users/mmarchini/workspace/nodejs/node/out/Release/phoenix"


class V8Context(object):
  def __init__(self):
    self._tmpdir = tempfile.mkdtemp()
    self.stdin = open(path.join(self._tmpdir, "stdin"), "w+")
    with open(path.join(self._tmpdir, "stdout"), "w+") as f:
      self.stdout = open(f.name, "r")
    self.current_line = 0

  # TODO delete temporary directory and files


def v8_load(debugger, args, result, internal_dict):
  debugger.SetAsync(True)

  error = lldb.SBError()

  host_target = debugger.CreateTarget(HOST)

  context = V8Context()

  # TODO support multiple targets
  internal_dict["v8_context"] = context

  launch_parameters = OrderedDict([
    ("listener", debugger.GetListener()),
    ("argv", [context.stdin.name, context.stdout.name]),
    ("envp", None),
    ("stdin_path", "/dev/null"),
    ("stdout_path", "/dev/null"),
    ("stderr_path", "/dev/null"),
    ("working_directory", None),
    ("launch_flags", 0),
    ("stop_at_entry", False),
    ("error", error),
  ])
  print launch_parameters
  host_process = host_target.Launch(*(launch_parameters.values()))

  if error.Fail():
    result.SetError(error)
    return False

  debugger.SetSelectedTarget(host_target)

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

  return True


def int_to_buffer(value):
  value = hex(value)[2:]

  # Fill zero in the left in hex has odd length
  value = value.rjust((len(value)/2 + 1) * 2, '0')


  # Split hex value into bytes (two hex digits)
  value_bytes = list(map(''.join, zip(*[iter(value)]*2)))

  # Convert bytes into chars and return

  return "".join([chr(int(v, 16)) for v in value_bytes])


def v8_stack(debugger, args, result, internal_dict):
  target = debugger.GetSelectedTarget()
  context = internal_dict["v8_context"]
  context.stdin.write("s\n")
  context.stdin.flush()

  # TODO have control character on stdout
  sleep(1)

  context.stdout.seek(context.current_line)
  lines = context.stdout.readlines()
  context.current_line = context.stdout.tell()
  print >>result, lines
  return True


def v8_print(debugger, args, result, internal_dict):
  target = debugger.GetSelectedTarget()
  context = internal_dict["v8_context"]
  context.stdin.write("p\n")
  context.stdin.flush()

  context.stdout.sync()
  print >>result, context.stdout.readlines()
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
