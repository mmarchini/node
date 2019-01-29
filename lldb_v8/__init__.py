#!/usr/bin/python

import lldb
import argparse
from functools import wraps

from .helpers import validate_hex
from .postmortem_host import PostmortemHost


def v8_load(debugger, args, result, internal_dict):
  debugger.SetAsync(True)

  postmortem_host = PostmortemHost(debugger)
  if postmortem_host.is_valid:
    # TODO support multiple targets
    internal_dict["v8_postmortem_host"] = postmortem_host

  return True


def v8_postmortem_host(func):
  @wraps(func)
  def v8_postmortem_host_wrapper(debugger, args, result, internal_dict):
    if not "v8_postmortem_host" in internal_dict:
      if not v8_load(debugger, args, result, internal_dict):
        return False
    postmortem_host = internal_dict["v8_postmortem_host"]
    return func(debugger, args, result, internal_dict, postmortem_host)
  return v8_postmortem_host_wrapper


@v8_postmortem_host
def v8_stack(debugger, args, result, internal_dict, postmortem_host):
  core_target = debugger.GetSelectedTarget()
  core_process = core_target.process
  thread = core_process.selected_thread
  print thread.frame[0]
  frame = thread.frame[0]

  stack_pointer = frame.FindRegister("rsp").unsigned
  program_counter = frame.FindRegister("rip").unsigned
  postmortem_host.send("s %d %d" % (stack_pointer, program_counter))

  stack = postmortem_host.listen()
  if stack:
    print stack
    return True
  return False


@v8_postmortem_host
def v8_print(debugger, args, result, internal_dict, postmortem_host):
  postmortem_host.send("p %x" % args.address)

  obj = postmortem_host.listen()
  if obj:
    print obj
    return True
  return False



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
