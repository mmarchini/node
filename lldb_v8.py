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
from tempfile import NamedTemporaryFile
from collections import OrderedDict

HOST = "./out/Release/phoenix"


class V8Context(object):
  def __init__(self):
    self._tmpdir = tempfile.mkdtemp()
    self.stdin = open(path.join(self._tmpdir, "stdin"), "wb+")
    with open(path.join(self._tmpdir, "stdout"), "w+") as f:
      self.stdout = open(f.name, "r")
    with open(path.join(self._tmpdir, "host_stdout"), "w+") as f:
      self.host_stdout = open(f.name, "r")
    self.current_line = 0
    self.host_stdout_current_line = 0

  # TODO delete temporary directory and files


def v8_load(debugger, args, result, internal_dict):
  debugger.SetAsync(True)

  error = lldb.SBError()

  core_target = debugger.GetSelectedTarget()

  host_target = debugger.CreateTarget(HOST)

  context = V8Context()

  # TODO support multiple targets
  internal_dict["v8_context"] = context

  launch_parameters = OrderedDict([
    ("listener", debugger.GetListener()),
    ("argv", [context.stdin.name, context.stdout.name]),
    ("envp", None),
    ("stdin_path", "/dev/null"),
    ("stdout_path", context.host_stdout.name),
    # TODO (mmarchini): maybe it's better to supress stdout, and have separate
    # IPC channels to communication and output
    #  ("stdout_path", None),
    ("stderr_path", "/tmp/stderr"),
    ("working_directory", None),
    ("launch_flags", 0),
    ("stop_at_entry", False),
    ("error", error),
  ])
  host_process = host_target.Launch(*(launch_parameters.values()))

  if error.Fail():
    result.SetError(error)
    return False

  core_process = core_target.LoadCore(args.core_path)
  #  core_target = debugger.CreateTarget(args.core_path)

  context.host_target = host_target
  context.host_process = host_process

  if error.Fail():
    result.SetError(error)
    return False

  memory_ranges = core_process.GetMemoryRegions()
  memory_info = lldb.SBMemoryRegionInfo()

  regions = 0
  failures = 0

  for i in range(memory_ranges.GetSize()):
    if not memory_ranges.GetMemoryRegionAtIndex(i, memory_info):
      print >>result, "Range unavailable:", i

    if not memory_info.IsReadable():
      continue

    regions += 1

    addr = memory_info.GetRegionBase()
    range_len = memory_info.GetRegionEnd() - addr

    content = bytes(core_process.ReadMemory(addr, range_len, error))
    if error.Fail():
      result.SetError(error)
      return False

    # hex() will append a L at the end of the string if the number is large, so
    # we use "%x" instead
    filename = path.join(context._tmpdir, "%x" % addr)

    # TODO store file path in context
    with open(filename, "wb+") as f:
      f.write(content)
      f.flush()
      os.chmod(filename, 0744)

    message = "%x %d %s" % (addr, range_len, filename)
    context.stdin.write(message)
    context.stdin.flush()

    ret = None
    while not ret:
      context.stdout.seek(context.current_line)
      ret = "".join(context.stdout.readlines())
      context.current_line = context.stdout.tell()

    ret = int(ret)
    if ret != range_len:
      failures += 1
      print "Wrong size written: %s != %s" % (range_len, ret)
      # TODO remove file if not mapped
      #  os.remove(filename)

  context.stdin.write("done")
  context.stdin.flush()

  debugger.SetSelectedTarget(core_target)

  print >>result, "%d Regions (%d Failed)" % (regions, failures)

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
  context = internal_dict["v8_context"]

  core_target = debugger.GetSelectedTarget()
  core_process = core_target.process

  top_frame = core_process.selected_thread.frame[0]

  stack_pointer = top_frame.FindRegister("rsp").unsigned
  program_counter = top_frame.FindRegister("rip").unsigned

  context.stdin.write("s %d %d\n" % (stack_pointer, program_counter))
  context.stdin.flush()

  print stack_pointer, program_counter

  while True:
    context.stdout.seek(context.current_line)
    request = "".join([line.rstrip('\n') for line in context.stdout.readlines()])
    context.current_line = context.stdout.tell()

    if not request:
      continue

    if request == "end":
      break

    if request.startswith("GetRegister"):
      register = request.split(" ")[1]
      reg_value = top_frame.FindRegister(register).unsigned
      context.stdin.write(int_to_buffer(reg_value))
      context.stdin.write("\n")
    elif request.startswith("GetStaticData"):
      name = request.split(" ")[1]
      print name
      print core_target.FindGlobalVariables(name, 2)
      print core_target.FindSymbols(name, 2)

  context.host_stdout.seek(context.host_stdout_current_line)
  lines = "\n".join(context.host_stdout.readlines())
  context.host_stdout_current_line = context.host_stdout.tell()
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
