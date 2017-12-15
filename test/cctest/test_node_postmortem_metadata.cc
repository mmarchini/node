#include "node_postmortem_metadata.cc"

#include "gtest/gtest.h"
#include "node.h"
#include "node_internals.h"
#include "node_test_fixture.h"
#include "req_wrap-inl.h"
#include "tracing/agent.h"
#include "v8.h"

const int node::Environment::kContextEmbedderDataIndex;


class DebugSymbolsTest : public EnvironmentTestFixture {};


class TestHandleWrap : public node::HandleWrap {
 public:
  size_t self_size() const override { return sizeof(*this); }

  TestHandleWrap(node::Environment* env,
                 v8::Local<v8::Object> object,
                 uv_handle_t* handle)
      : node::HandleWrap(env,
                         object,
                         handle,
                         node::AsyncWrap::PROVIDER_TIMERWRAP) {}
};


class TestReqWrap : public node::ReqWrap<uv_req_t> {
 public:
  size_t self_size() const override { return sizeof(*this); }

  TestReqWrap(node::Environment* env, v8::Local<v8::Object> object)
      : node::ReqWrap<uv_req_t>(env,
                                object,
                                node::AsyncWrap::PROVIDER_TIMERWRAP) {}
};

TEST_F(DebugSymbolsTest, ContextEmbedderDataIndex) {
  EXPECT_EQ(nodedbg_const_Environment__kContextEmbedderDataIndex,
            node::Environment::kContextEmbedderDataIndex);
}

TEST_F(DebugSymbolsTest, BaseObjectPersistentHandle) {
  const v8::HandleScope handle_scope(isolate_);
  const Argv argv;
  Env env{handle_scope, argv, this};

  v8::Local<v8::Object> object = v8::Object::New(isolate_);
  node::BaseObject obj(*env, object);

  auto expected = reinterpret_cast<uintptr_t>(&obj.persistent());
  auto calculated = reinterpret_cast<uintptr_t>(&obj) +
      nodedbg_offset_BaseObject__persistent_handle_;
  EXPECT_EQ(expected, calculated);

  obj.persistent().Reset();  // ~BaseObject() expects an empty handle.
}


TEST_F(DebugSymbolsTest, EnvironmentHandleWrapQueue) {
  const v8::HandleScope handle_scope(isolate_);
  const Argv argv;
  Env env{handle_scope, argv, this};

  auto expected = reinterpret_cast<uintptr_t>((*env)->handle_wrap_queue());
  auto calculated = reinterpret_cast<uintptr_t>(*env) +
      nodedbg_offset_Environment__handle_wrap_queue_;
  EXPECT_EQ(expected, calculated);
}

TEST_F(DebugSymbolsTest, EnvironmentReqWrapQueue) {
  const v8::HandleScope handle_scope(isolate_);
  const Argv argv;
  Env env{handle_scope, argv, this};

  auto expected = reinterpret_cast<uintptr_t>((*env)->req_wrap_queue());
  auto calculated = reinterpret_cast<uintptr_t>(*env) +
      nodedbg_offset_Environment__req_wrap_queue_;
  EXPECT_EQ(expected, calculated);
}

TEST_F(DebugSymbolsTest, HandleWrapList) {
  const v8::HandleScope handle_scope(isolate_);
  const Argv argv;
  Env env{handle_scope, argv, this};

  uv_handle_t handle;

  node::tracing::TraceEventHelper::SetTracingController(
      new v8::TracingController());

  auto obj_template = v8::FunctionTemplate::New(isolate_);
  obj_template->InstanceTemplate()->SetInternalFieldCount(1);

  v8::Local<v8::Object> object =
      obj_template->GetFunction()->NewInstance(env.context()).ToLocalChecked();
  auto* obj = new TestHandleWrap(*env, object, &handle);

  auto queue = reinterpret_cast<uintptr_t>((*env)->handle_wrap_queue());
  auto head = queue + nodedbg_offset_HandleWrapQueue__head_;
  auto next = head + nodedbg_offset_ListNode_HandleWrap__next_;
  next = *reinterpret_cast<uintptr_t*>(next);

  auto expected = reinterpret_cast<uintptr_t>(obj);
  auto calculated = next - nodedbg_offset_HandleWrap__handle_wrap_queue_;
  EXPECT_EQ(expected, calculated);
}

TEST_F(DebugSymbolsTest, ReqWrapList) {
  const v8::HandleScope handle_scope(isolate_);
  const Argv argv;
  Env env{handle_scope, argv, this};

  node::tracing::TraceEventHelper::SetTracingController(
      new v8::TracingController());

  auto obj_template = v8::FunctionTemplate::New(isolate_);
  obj_template->InstanceTemplate()->SetInternalFieldCount(1);

  v8::Local<v8::Object> object =
      obj_template->GetFunction()->NewInstance(env.context()).ToLocalChecked();
  auto* obj = new TestReqWrap(*env, object);

  auto queue = reinterpret_cast<uintptr_t>((*env)->req_wrap_queue());
  auto head = queue + nodedbg_offset_ReqWrapQueue__head_;
  auto next = head + nodedbg_offset_ListNode_ReqWrap__next_;
  next = *reinterpret_cast<uintptr_t*>(next);

  auto expected = reinterpret_cast<uintptr_t>(obj);
  auto calculated = next - nodedbg_offset_ReqWrap__req_wrap_queue_;
  EXPECT_EQ(expected, calculated);
}
