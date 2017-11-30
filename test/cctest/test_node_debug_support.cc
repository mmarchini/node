/* {{debug_symbols_file}} */

/*
 * This file is a template used by ./tools/gen-postmortem-metadata.py to
 * generate a proper test file
 */

#include "gtest/gtest.h"
#include "../../../../test/cctest/node_test_fixture.h"
#include "node.h"
#include "node_internals.h"
#include "udp_wrap.h"
#include "v8.h"
#include "tracing/agent.h"

const int node::Environment::kContextEmbedderDataIndex;


class DebugSymbolsTest : public EnvironmentTestFixture {
};


class TestHandleWrap : public node::HandleWrap {
  public:
   size_t self_size() const override { return sizeof(*this); }

   TestHandleWrap(node::Environment* env, v8::Local<v8::Object> object, uv_handle_t* handle) :
     node::HandleWrap(env, object, handle, node::AsyncWrap::PROVIDER_TIMERWRAP) {}
};


TEST_F(DebugSymbolsTest, ContextEmbedderDataIndex) {
  EXPECT_EQ(nodedbg_environment_context_idx_embedder_data, node::Environment::kContextEmbedderDataIndex);
}

TEST_F(DebugSymbolsTest, BaseObjectPersistentHandle) {
  const v8::HandleScope handle_scope(isolate_);
  const Argv argv;
  Env env {handle_scope, isolate_, argv, this};

  v8::Local<v8::Object> object = v8::Object::New(isolate_);
  node::BaseObject *obj = new node::BaseObject(*env, object);

  auto expected = (uintptr_t)&(obj->persistent());
  auto calculated = (uintptr_t)((void*)obj) + nodedbg_class__BaseObject__persistent_handle;
  EXPECT_EQ(expected, calculated);
}


TEST_F(DebugSymbolsTest, EnvironmentHandleWrapQueue) {
  const v8::HandleScope handle_scope(isolate_);
  const Argv argv;
  Env env {handle_scope, isolate_, argv, this};

  auto expected = (uintptr_t)((*env)->handle_wrap_queue());
  auto calculated = ((uintptr_t)(*env)) + + nodedbg_class__Environment__handleWrapQueue;
  EXPECT_EQ(expected, calculated);
}

TEST_F(DebugSymbolsTest, EnvironmentReqWrapQueue) {
  const v8::HandleScope handle_scope(isolate_);
  const Argv argv;
  Env env {handle_scope, isolate_, argv, this};

  // auto l = (*env)->req_wrap_queue();
  // EXPECT_EQ((void *)((*env)->req_wrap_queue()), (((void*)(*env)) + nodedbg_class__Environment__reqWrapQueue));
}

TEST_F(DebugSymbolsTest, HandleWrapList) {
  v8::HandleScope handle_scope(isolate_);
  auto context = node::NewContext(isolate_);
  v8::Context::Scope context_scope(context);
  node::IsolateData* isolateData = node::CreateIsolateData(isolate_, uv_default_loop());
  Argv argv{"node", "-e", ";"};
  auto env = node::CreateEnvironment(isolateData, context, 1, *argv, 2, *argv);

  uv_handle_t handle_;

  node::tracing::TraceEventHelper::SetTracingController(
    new v8::TracingController());

  auto obj_template = v8::FunctionTemplate::New(isolate_);
  obj_template->SetClassName(FIXED_ONE_BYTE_STRING(isolate_, "prop1"));
  obj_template->InstanceTemplate()->SetInternalFieldCount(1);

  v8::Local<v8::Object> object = obj_template->GetFunction()->NewInstance(context).ToLocalChecked();
  std::cout << "aaa 1" << std::endl;
  auto *obj = new TestHandleWrap(env, object, &handle_);
}
