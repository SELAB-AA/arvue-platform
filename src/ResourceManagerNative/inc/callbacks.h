#ifndef CALLBACKS_H
#define CALLBACKS_H

#include "macros.h"
#include "jni.h"
#include "jvmti.h"
void JNICALL RESOURCE_MANAGER_native_newobj(JNIEnv *env, jclass klass, jthread thread, jobject o);
void JNICALL RESOURCE_MANAGER_native_newarr(JNIEnv *env, jclass klass, jthread thread, jobject a);
void JNICALL cbThreadStart(jvmtiEnv *jvmti, JNIEnv *env, jthread thread);
void JNICALL cbThreadEnd(jvmtiEnv *jvmti, JNIEnv *env, jthread thread);
void JNICALL cbVMObjectAlloc(jvmtiEnv *jvmti, JNIEnv *env, jthread thread, jobject o, jclass object_klass, jlong size);
void JNICALL cbObjectFree(jvmtiEnv *jvmti, jlong tag);
#endif
