import re
import argparse


# TODO(mmarchini) use Python logger?
def logger(*args):
  args = map(str, args)
  print "[lldb_v8] ", " ".join(args)


def int_to_buffer(value):
  value = hex(value)[2:]

  # Fill zero in the left in hex has odd length
  value = value.rjust((len(value)/2 + 1) * 2, '0')

  # Split hex value into bytes (two hex digits)
  value_bytes = list(map(''.join, zip(*[iter(value)]*2)))

  # Convert bytes into chars and return

  return "".join([chr(int(v, 16)) for v in value_bytes])


HEX_RE = re.compile(r"^(?:0x){0,1}[0-9a-f]+")
def validate_hex(val):
  match = HEX_RE.match(val)
  if not match:
      raise argparse.ArgumentTypeError
  return int(val, 16)
