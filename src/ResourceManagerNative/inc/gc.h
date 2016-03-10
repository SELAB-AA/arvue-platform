#ifndef GC_H
#define GC_H

#include "jvmti.h"

void JNICALL gc_thread(jvmtiEnv* jvmti, JNIEnv* jni, void *p);

#endif
