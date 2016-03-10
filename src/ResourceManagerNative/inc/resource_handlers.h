#ifndef RESOURCE_HANDLERS_H
#define RESOURCE_HANDLERS_H

#include "data_utils.h"

void checkThreadLimits(jvmtiEnv *jvmti,  JNIEnv* env, jthread thread, SessionInfo *sinfo);
void checkMemoryLimits(jvmtiEnv *jvmti,  JNIEnv* env, jthread thread, SessionInfo *sinfo);
void checkCPULimits(jvmtiEnv *jvmti,  JNIEnv* env, jthread thread, long long threadTime, SessionInfo* sinfo);

#endif
