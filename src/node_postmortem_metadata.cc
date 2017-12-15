// Need to import standard headers before redefining private, otherwise it
// won't compile
#include <algorithm>
#include <array>
#include <atomic>
#include <bitset>
#include <cctype>
#include <climits>
#include <cmath>
#include <cstdarg>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <deque>
#include <exception>
#include <forward_list>
#include <fstream>
#include <functional>
#include <iomanip>
#include <iosfwd>
#include <iostream>
#include <istream>
#include <iterator>
#include <limits>
#include <list>
#include <map>
#include <memory>
#include <new>
#include <ostream>
#include <queue>
#include <set>
#include <sstream>
#include <stack>
#include <streambuf>
#include <string>
#include <tuple>
#include <type_traits>
#include <typeinfo>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

namespace node {
// Forward declaration needed before redefining private
int GenDebugSymbol();
}  // namespace node


#define private friend int GenDebugSymbol(); private

#include "env.h"
#include "base_object-inl.h"
#include "handle_wrap.h"
#include "util-inl.h"
#include "req_wrap.h"

// These are the constants describing Node internal structures. Every constant
// should use the following format:
//
//    nodedbg_const_CLASS__MEMBER      Describes a class member constant
//    nodedbg_offset_CLASS__MEMBER     Describes the offset to a class member
//
// These constants are declared as global integers so that they'll be present in
// the generated node binary. They also need to be declared outside any
// namespace to avoid C++ name-mangling.
uintptr_t nodedbg_offset_BaseObject__persistent_handle_;

int nodedbg_const_Environment__kContextEmbedderDataIndex;
uintptr_t nodedbg_offset_Environment__handle_wrap_queue_;
uintptr_t nodedbg_offset_Environment__req_wrap_queue_;

uintptr_t nodedbg_offset_HandleWrap__handle_wrap_queue_;
uintptr_t nodedbg_offset_HandleWrapQueue__head_;
uintptr_t nodedbg_offset_ListNode_HandleWrap__next_;

uintptr_t nodedbg_offset_ReqWrap__req_wrap_queue_;
uintptr_t nodedbg_offset_ReqWrapQueue__head_;
uintptr_t nodedbg_offset_ListNode_ReqWrap__next_;

namespace node {

int GenDebugSymbol() {
  nodedbg_offset_BaseObject__persistent_handle_ =
      OffsetOf(&BaseObject::persistent_handle_);

  nodedbg_const_Environment__kContextEmbedderDataIndex =
      Environment::kContextEmbedderDataIndex;
  nodedbg_offset_Environment__handle_wrap_queue_ =
      OffsetOf(&Environment::handle_wrap_queue_);
  nodedbg_offset_Environment__req_wrap_queue_ =
      OffsetOf(&Environment::req_wrap_queue_);

  nodedbg_offset_HandleWrap__handle_wrap_queue_ =
      OffsetOf(&HandleWrap::handle_wrap_queue_);
  nodedbg_offset_HandleWrapQueue__head_ =
      OffsetOf(&Environment::HandleWrapQueue::head_);
  nodedbg_offset_ListNode_HandleWrap__next_ =
      OffsetOf(&ListNode<HandleWrap>::next_);

  nodedbg_offset_ReqWrap__req_wrap_queue_ =
      OffsetOf(&ReqWrap<uv_req_t>::req_wrap_queue_);
  nodedbg_offset_ReqWrapQueue__head_ =
      OffsetOf(&Environment::ReqWrapQueue::head_);
  nodedbg_offset_ListNode_ReqWrap__next_ =
      OffsetOf(&ListNode<ReqWrap<uv_req_t>>::next_);
  return 1;
}

int debug_symbols_generated = GenDebugSymbol();

}  // namespace node
