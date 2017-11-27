# Debug Symbols

Debug symbols are constants present in the final build which can be used by
debuggers or other scripts to navigate internal structures of the software when
analyzing its memory. This is useful when doing postmortem analysis, for
example. Node provides debug symbols in its builds for V8 and Node internal
structures.

## V8 Debug Symbols

All symbols available for V8 are prefixed with `v8dbg_`, and they allow inspection
of objects in the heap as well as those object's properties and references. Those
symbols are provided by V8 itself by the script
`deps/v8/tools/gen-postmortem-metadata.py`.

## Node Debug Symbols

All symbols available for Node internals are prefixed with `nodedbg_`, and they
complement V8 symbols by providing ways to inspect Node-specific strucutres,
like `node::Environment`, `node::AsyncWrap` and its descendents, objects from
`utils.h` and others. Those symbols are provided by the script
`tools/gen-postmortem-metadata.py`.

## Tools using this

* [https://github.com/nodejs/llnode](llnode): LLDB plugin
* [https://github.com/joynet/mdb_v8](mdb_v8): mdb plugin
