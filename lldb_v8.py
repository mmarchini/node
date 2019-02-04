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


# TODO(mmarchini) use Python logger?
def logger(*args):
  print "[lldb_v8] ", " ".join(args)


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


def int_to_buffer(value):
  value = hex(value)[2:]

  # Fill zero in the left in hex has odd length
  value = value.rjust((len(value)/2 + 1) * 2, '0')


  # Split hex value into bytes (two hex digits)
  value_bytes = list(map(''.join, zip(*[iter(value)]*2)))

  # Convert bytes into chars and return

  return "".join([chr(int(v, 16)) for v in value_bytes])


def v8_load(debugger, args, result, internal_dict):
  debugger.SetAsync(True)

  error = lldb.SBError()

  # TODO add some checks
  core_target = debugger.GetSelectedTarget()
  core_process = core_target.process

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
      logger("Couldn't write region [0x%x, 0x%x)" % (addr, addr + range_len))
      logger("Wrong size written: %s != %s" % (range_len, ret))
      # TODO remove file if not mapped
      #  os.remove(filename)

  context.stdin.write("done")
  context.stdin.flush()

  debugger.SetSelectedTarget(core_target)

  print >>result, "%d Regions (%d Failed)" % (regions, failures)

  return True


def v8_context(func):
  def v8_context_wrapper(debugger, args, result, internal_dict):
    if not "v8_context" in internal_dict:
      if not v8_load(debugger, args, result, internal_dict):
        return False
    context = internal_dict["v8_context"]
    return func(debugger, args, result, internal_dict, context)
  return v8_context_wrapper


@v8_context
def v8_stack(debugger, args, result, internal_dict, context):
  core_target = debugger.GetSelectedTarget()
  core_process = core_target.process

  top_frame = core_process.selected_thread.frame[0]

  stack_pointer = top_frame.FindRegister("rsp").unsigned
  program_counter = top_frame.FindRegister("rip").unsigned

  context.stdin.write("s %d %d\n" % (stack_pointer, program_counter))
  context.stdin.flush()

  while True:
    context.stdout.seek(context.current_line)
    request = "".join([line.rstrip('\n') for line in context.stdout.readlines()])
    context.current_line = context.stdout.tell()

    context.host_stdout.seek(context.host_stdout_current_line)
    lines = "\n".join(context.host_stdout.readlines())
    context.host_stdout_current_line = context.host_stdout.tell()
    if lines:
      print lines.strip("\n")

    if request == "end" or not context.host_process.is_running:
      break

    if not request:
      continue

    if request.startswith("GetRegister"):
      register = request.split(" ")[1]
      reg_value = top_frame.FindRegister(register).unsigned
      context.stdin.write(int_to_buffer(reg_value))
      context.stdin.write("\n")
      context.stdin.flush()
    elif request.startswith("GetStaticData"):
      byte_count, name = request.split(" ")[1:]
      byte_count = int(byte_count)
      logger(name)
      value = int_to_buffer(0)
      for m in core_target.module_iter():
        symbol = m.FindSymbol(name)
        if symbol:
          if symbol.end_addr.offset - symbol.addr.offset  != byte_count:
            logger("We're in a hard pickle, yes we are")
            continue
          error = lldb.SBError()
          try_value = core_target.ReadMemory(symbol.addr, byte_count, error)
          if error.Fail():
            logger("Oopsie doopsie!")
            continue
          value = try_value
          logger(value)
          break
      context.stdin.write(value)
      context.stdin.write("\n")
      context.stdin.flush()
    elif request.startswith("GetTlsData"):
      logger("Loading TLS data")
      key = int(request.split(" ")[1])
      logger("for key: %d" % key)

      value = TLSAccessor(debugger).getspecific(key)
      logger("Result: 0x%x" % value)

      context.stdin.write("%x" % value)
      context.stdin.write("\n")
      context.stdin.flush()

  context.host_stdout.seek(context.host_stdout_current_line)
  lines = "\n".join(context.host_stdout.readlines())
  context.host_stdout_current_line = context.host_stdout.tell()
  print >>result, lines
  return True


@v8_context
def v8_print(debugger, args, result, internal_dict, context):
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


class TLSAccessor(object):
  """
  0x7ffff6e7a030 <+0>:   cmpl   $0x1f, %edi
  0x7ffff6e7a033 <+3>:   ja     0x7ffff6e7a080            ; <+80>
  0x7ffff6e7a035 <+5>:   movl   %edi, %eax
  0x7ffff6e7a037 <+7>:   addq   $0x31, %rax
  0x7ffff6e7a03b <+11>:  shlq   $0x4, %rax
  0x7ffff6e7a03f <+15>:  movq   %fs:0x10, %rdx
  0x7ffff6e7a048 <+24>:  addq   %rax, %rdx
  0x7ffff6e7a04b <+27>:  movq   0x8(%rdx), %rax
  0x7ffff6e7a04f <+31>:  testq  %rax, %rax
  0x7ffff6e7a052 <+34>:  je     0x7ffff6e7a06a            ; <+58>
  0x7ffff6e7a054 <+36>:  movl   %edi, %edi
  0x7ffff6e7a056 <+38>:  leaq   0x20b2c3(%rip), %rcx      ; __GI___pthread_keys
  0x7ffff6e7a05d <+45>:  movq   (%rdx), %rsi
  0x7ffff6e7a060 <+48>:  shlq   $0x4, %rdi
  0x7ffff6e7a064 <+52>:  cmpq   %rsi, (%rcx,%rdi)
  0x7ffff6e7a068 <+56>:  jne    0x7ffff6e7a070            ; <+64>
  0x7ffff6e7a06a <+58>:  rep    retq
  0x7ffff6e7a06c <+60>:  nopl   (%rax)
  0x7ffff6e7a070 <+64>:  movq   $0x0, 0x8(%rdx)
  0x7ffff6e7a078 <+72>:  xorl   %eax, %eax
  0x7ffff6e7a07a <+74>:  retq
  0x7ffff6e7a07b <+75>:  nopl   (%rax,%rax)
  0x7ffff6e7a080 <+80>:  cmpl   $0x3ff, %edi              ; imm = 0x3FF
  0x7ffff6e7a086 <+86>:  ja     0x7ffff6e7a0b0            ; <+128>
  0x7ffff6e7a088 <+88>:  movl   %edi, %eax
  0x7ffff6e7a08a <+90>:  movl   %edi, %edx
  0x7ffff6e7a08c <+92>:  andl   $0x1f, %eax
  0x7ffff6e7a08f <+95>:  shrl   $0x5, %edx
  0x7ffff6e7a092 <+98>:  movq   %fs:0x510(,%rdx,8), %rcx
  0x7ffff6e7a09b <+107>: testq  %rcx, %rcx
  0x7ffff6e7a09e <+110>: je     0x7ffff6e7a0b0            ; <+128>
  0x7ffff6e7a0a0 <+112>: shlq   $0x4, %rax
  0x7ffff6e7a0a4 <+116>: leaq   (%rcx,%rax), %rdx
  0x7ffff6e7a0a8 <+120>: jmp    0x7ffff6e7a04b            ; <+27>
  0x7ffff6e7a0aa <+122>: nopw   (%rax,%rax)
  0x7ffff6e7a0b0 <+128>: xorl   %eax, %eax
  0x7ffff6e7a0b2 <+130>: retq
  """

  def __init__(self, debugger):
    self.debugger = debugger


  def getspecific(self, key):
    """
    __pthread_getspecific (glibc 2.27):

    void *
    __pthread_getspecific (pthread_key_t key)
    {
      struct __pthread *self;

      if (key < 0 || key >= __pthread_key_count
          || __pthread_key_destructors[key] == PTHREAD_KEY_INVALID)
        return NULL;

      self = _pthread_self ();
      if (key >= self->thread_specifics_size)
        return 0;

      return self->thread_specifics[key];
    }
    """

    interpreter = self.debugger.GetCommandInterpreter()
    # https://stackoverflow.com/a/10859835/2956796
    command_line = "p ((struct pthread*)0x%x)->specific[%d/32][%d%%32]" % (self._pthread_self, key, key)
    result = lldb.SBCommandReturnObject()
    result_status = interpreter.HandleCommand(command_line, result)
    print result.GetOutput()
    print result.GetError()
    print re.compile("data = (0x[0-9a-fA-F]+)").search(result.GetOutput())
    print re.compile("data = (0x[0-9a-fA-F]+)").search(result.GetOutput()).group(1)
    print int(re.compile("data = (0x[0-9a-fA-F]+)").search(result.GetOutput()).group(1), 16)

    return int(re.compile("data = (0x[0-9a-fA-F]+)").search(result.GetOutput()).group(1), 16)

    #  if key < 0 or key >= pthread_key_count or pthread_key_destructors[key] == PTHREAD_KEY_INVALID:
      #  return 0

    #  if key >= self.thread_specifics_size:
      #  return 0

    #  return self.thread_specifics(key)

  @property
  def _pthread_self(self):
    """
    __thread struct __pthread *___pthread_self;
    """
    # 0x7ffff6e7a03f <+15>:  movq   %fs:0x10, %rdx

    target = self.debugger.GetSelectedTarget()
    process = target.process
    top_frame = process.selected_thread.frame[0]

    return top_frame.FindRegister("fs_base").unsigned




def v8_handler(debugger, command, result, internal_dict):
  v8_parser = argparse.ArgumentParser(prog='v8', description='v8-related commands')
  subparsers = v8_parser.add_subparsers()

  load_parser = subparsers.add_parser('load')
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
