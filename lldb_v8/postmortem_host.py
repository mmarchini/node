import os
from time import sleep
import tempfile
from os import path
from functools import wraps
from collections import OrderedDict

import lldb

from .helpers import int_to_buffer, logger
from .tls import TLSAccessor

def ipc_call(ipc_method, ipc_args):
  def ipc_call_decorator(func):
    @wraps(func)
    def ipc_call_wrapper(*args):
      return func(args[0], *[ipc_args[i](args[i + 1]) for i in range(len(ipc_args))])
    ipc_call_wrapper._ipc_method = ipc_method
    return ipc_call_wrapper
  return ipc_call_decorator


class PostmortemHost(object):
  def __init__(self, debugger):
    self.debugger = debugger
    self.is_valid = False
    self.create_ipc_files()
    if self.create_host_process():
      self.is_valid = self.load_core_memory_on_host_process()

  @property
  def ipc_methods(self):
    ipc_methods = {}
    for name in dir(self):
      if name == "ipc_methods":
        continue
      attr = getattr(self, name, None)
      if hasattr(attr, "_ipc_method"):
        ipc_methods[attr._ipc_method] = attr
    return ipc_methods

  def create_host_process(self):
    # TODO add some checks
    self.core_target = self.debugger.GetSelectedTarget()
    self.core_process = self.core_target.process

    self.host_target = self.debugger.CreateTarget(self.core_target.executable.fullpath)

    error = lldb.SBError()
    launch_parameters = OrderedDict([
      ("listener", self.debugger.GetListener()),
      ("argv",
        ["--experimental-postmortem-host", self.stdin.name, self.stdout.name]),
      ("envp", None),
      ("stdin_path", "/dev/null"),
      ("stdout_path", "/dev/null"),
      ("stderr_path", "/tmp/stderr"),
      ("working_directory", None),
      ("launch_flags", 0),
      ("stop_at_entry", False),
      ("error", error),
    ])
    self.host_process = self.host_target.Launch(*(launch_parameters.values()))

    if error.Fail() or not self.host_process.IsValid():
      logger(error)
      return False

    retries = 5
    while not self.host_process.is_running:
      if retries == 0:
        logger("Host process is not running")
        return False
      retries -= 1
      sleep(1)

    return True

  def load_core_memory_on_host_process(self):
    error = lldb.SBError()
    memory_ranges = self.core_process.GetMemoryRegions()
    memory_info = lldb.SBMemoryRegionInfo()

    regions = 0
    failures = 0

    for i in range(memory_ranges.GetSize()):
      if not memory_ranges.GetMemoryRegionAtIndex(i, memory_info):
        logger("Range unavailable: ", i)

      if not (memory_info.IsReadable() or memory_info.IsExecutable()):
        continue

      regions += 1

      addr = memory_info.GetRegionBase()
      range_len = memory_info.GetRegionEnd() - addr

      content = bytes(self.core_process.ReadMemory(addr, range_len, error))
      if error.Fail():
        logger(error)
        continue

      if len(content) != range_len:
        logger("Wrong read size")
        continue

      filename = path.join(self._tmpdir, "%x" % addr)

      # TODO store file path in context
      with open(filename, "wb+") as f:
        f.write(content)
        f.flush()
        os.chmod(filename, 0744)

      message = "%x %d %s" % (addr, range_len, filename)
      self.send(message)

      ret = int(self.receive())
      if ret != range_len:
        failures += 1
        logger("Couldn't write region [0x%x, 0x%x)" % (addr, addr + range_len))
        logger("Wrong size written: %s != %s" % (range_len, ret))
        os.remove(filename)

    self.send("done")

    self.debugger.SetSelectedTarget(self.core_target)

    print "%d Memory Regions loaded (%d Failed)" % (regions, failures)
    return True

  def create_ipc_files(self):
    self._tmpdir = tempfile.mkdtemp()

    self.stdin = open(path.join(self._tmpdir, "stdin"), "wb+")

    with open(path.join(self._tmpdir, "stdout"), "w+") as f:
      self.stdout = open(f.name, "r")
    self.current_line = 0
    self._stdout_buffer = []

  def send(self, msg):
    self.stdin.write(msg)
    self.stdin.write("\n")
    self.stdin.flush()

  def receive(self):
    if self._stdout_buffer:
      return self._stdout_buffer.pop(0)

    while True:
      if not self.host_process.is_running:
        return None

      self.stdout.seek(self.current_line)
      lines = self.stdout.readlines()
      if not (lines and lines[-1].endswith("\n")):
        continue

      self.current_line = self.stdout.tell()
      self._stdout_buffer = [line.rstrip('\n') for line in lines]
      return self.receive()

  @ipc_call("GetRegister", [str])
  def get_register(register, frame):
    top_frame = self.core_process.selected_thread.frame[0]
    reg_value = top_frame.FindRegister(register).unsigned
    return "0x%x" % reg_value

  @ipc_call("GetStaticData", [int, str])
  def get_static_data(self, byte_count, name):
    value = "00" * byte_count
    for m in self.core_target.module_iter():
      symbol = m.FindSymbol(name)
      if symbol:
        if symbol.end_addr.offset - symbol.addr.offset  != byte_count:
          logger("We're in a hard pickle, yes we are")
          continue
        error = lldb.SBError()
        maybe_value = self.core_target.ReadMemory(symbol.addr, byte_count, error)
        if error.Fail():
          logger("Oopsie doopsie!")
          continue
        value = "".join([("%x" % ord(c)).zfill(2) for c in maybe_value])
        break
    return value

  @ipc_call("GetTlsData", [int])
  def get_tls_data(self, key):
    return "%x" % TLSAccessor(self.debugger).getspecific(key)

  def listen(self):
    while True:
      request = self.receive()

      if not self.host_process.is_running:
        return False

      if not request:
        continue

      if request == "end":
        break

      if request.startswith("return"):
        return request.split(" ", 1)[1]

      ipc_method = self.ipc_methods.get(request.split(" ")[0], None)
      if ipc_method:
        self.send(ipc_method(*request.split(" ")[1:]))

    return True

  # TODO cleanup everything (files, target, process, etc.)
  def __delete__(self):
    pass
