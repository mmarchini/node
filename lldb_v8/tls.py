import re
import lldb

TLS_DATA_RE = re.compile("data = (0x[0-9a-fA-F]+)")

class TLSAccessor(object):
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

    if not result.Succeeded():
      print "Couldn't read TLS data for key %d" % key
      return 0
    search_result = TLS_DATA_RE.search(result.GetOutput())
    if not search_result:
      print "Couldn't parse TLS data for key %d" % key
      return 0

    return int(search_result.group(1), 16)

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
