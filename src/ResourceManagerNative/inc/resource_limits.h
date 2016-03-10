#ifndef RESOURCE_LIMITS_H
#define RESOURCE_LIMITS_H

#include "jni.h"
#include "jvmti.h"


typedef struct LimitInfo {
	jlong memUsageLimit;
	jlong cpuUsageLimit;
	jlong cpuThreadUsageLimit;
	jint noThreadsLimit;
	jint maxInterrupts;
} LimitInfo;

typedef struct LimitInfoEx {
	LimitInfo info;
	const char* pattern;
	struct LimitInfoEx* next;
} LimitInfoEx;

const LimitInfo* getLimits(const char* sessionCode);
void loadLimits(const char* filename);

#endif
