#ifndef DATA_UTILS_H
#define DATA_UTILS_H

#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <stddef.h>
#include <limits.h>
#include <time.h>

#include "jni.h"
#include "jvmti.h"

#include "resource_limits.h"

/* Global agent data structure */



typedef struct SessionInfo {
	jint hashCode;
	char* sessionId;
	jlong memUsage;
	jlong cpuUsage;
	jint noThreads;
	jint interrupts;
	time_t timestamp;
	const LimitInfo* limits;
	/* Pointers for linked list */
	struct SessionInfo* prev;
	struct SessionInfo* next;
	unsigned int index; // Index to HashTable
} SessionInfo;

/* Number of bits for hash index */
#define HASH_SIZE 10

/* Tag structure for allocated objects */
typedef struct TagInfo {
	jlong size;
	jint hashCode;
	jint groupHashCode;
	jlong cputime;
} TagInfo;

// typedef jint ThreadGroupInfo;

typedef struct {
    /* JVMTI Environment */
    jvmtiEnv      *jvmti;
    /* State of the VM flags */
    jboolean       vmStarted;
    jboolean       vmInitialized;
    jboolean       vmDead;
    /* Options */

    /* Data access Lock */
    jrawMonitorID  lock;
    jrawMonitorID	threadLock, gcLock;
    /* Counter on classes where BCI has been applied */
    jint           ccount;
    jboolean nomem, nocpu, nolimits,nothreads;
    char limitfile[PATH_MAX];
    char logfile[PATH_MAX];
    /* Limits */
    LimitInfoEx* limitInfos;
	/* Hash table */
    jint info_count;
    SessionInfo* sessionsHead[1<<HASH_SIZE];
} GlobalAgentData;


SessionInfo * newSessionInfo(unsigned int index, jint hashCode, const char* sessionCode);
SessionInfo * lookupOrEnter(jvmtiEnv *jvmti, jint hashCode, const char* sessionId);
SessionInfo * findSessionInfo(jvmtiEnv *jvmti, JNIEnv *env, jthread thread, bool createnew);
void tagObjectWithTagInfo(jvmtiEnv *jvmti, jobject object, SessionInfo *sinfo, jlong size, jint groupcode);
void freeSessionInfo(SessionInfo* info);
void enterCriticalSection(jvmtiEnv *jvmti);
void exitCriticalSection(jvmtiEnv *jvmti);

#endif
