#ifndef THREAD_UTIL_H
#define THREAD_UTIL_H

#include "jvmti.h"



char* getThreadName(jvmtiEnv *jvmti, jthread thread);
void JNICALL worker(jvmtiEnv* jvmti, JNIEnv* jni, void *p);
#endif
