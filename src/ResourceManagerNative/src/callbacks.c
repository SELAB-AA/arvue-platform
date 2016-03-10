
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stddef.h>
#include <stdarg.h>

/* General JVM/Java functions, types and macros. */

#include <sys/types.h>
#include "resource_handlers.h"
#include "agent_util.h"
#include "callbacks.h"

#include "thread_utils.h"
extern  GlobalAgentData *gdata;

/* Java Native Method for Object.<init> */
void JNICALL
RESOURCE_MANAGER_native_newobj(JNIEnv *env, jclass klass, jthread thread, jobject o)
{
    SessionInfo *sinfo;
    jlong size;
    jvmtiError error;

    if ( gdata->vmDead ||!thread) {
        return;
    }
    sinfo = findSessionInfo(gdata->jvmti, env, thread,true);
    if (!sinfo) {
        	return;
    }
    error = (*(gdata->jvmti))->GetObjectSize(gdata->jvmti,o, &size);
    check_jvmti_error(gdata->jvmti, error, "Cannot get size");

    sinfo->memUsage+=size;

    tagObjectWithTagInfo(gdata->jvmti, o, sinfo,size,0);
    checkMemoryLimits(gdata->jvmti,env, thread,sinfo);
}

/* Java Native Method for newarray */
void JNICALL
RESOURCE_MANAGER_native_newarr(JNIEnv *env, jclass klass, jthread thread, jobject a)
{
	  SessionInfo *sinfo;
	    jlong size;
	    jvmtiError error;

    if ( gdata->vmDead ||!thread) {
        return;
    }
    sinfo = findSessionInfo(gdata->jvmti, env, thread,true);
    if (!sinfo) {
    	return;
    }
    error = (*(gdata->jvmti))->GetObjectSize(gdata->jvmti,a, &size);
    check_jvmti_error(gdata->jvmti, error, "Cannot get array size");
    sinfo->memUsage+=size;
    tagObjectWithTagInfo(gdata->jvmti, a, sinfo,size,0);
	checkMemoryLimits(gdata->jvmti,env, thread,sinfo);
}


/*
 * Callback for JVMTI_THREAD_START
 * Hash value for the thread group should be saved for JVMTI_THREAD_STOP
 *
 */
void JNICALL
cbThreadStart(jvmtiEnv *jvmti, JNIEnv *env, jthread thread)
{
	SessionInfo* sinfo;
	  jvmtiError error;
	  TagInfo *tinfo;
	  jlong tag;
    if ( gdata->vmDead || !thread) {
        return;
    }
 	  sinfo = findSessionInfo(jvmti, env, thread,true);
 	  if (sinfo) {
 		  sinfo->noThreads++;
 		  error= (*jvmti)->GetTag(jvmti,thread,&tag);
 		  check_jvmti_error(gdata->jvmti, error, "Cannot get tag");
 		  if (!tag) {
 			 tagObjectWithTagInfo(gdata->jvmti, thread, sinfo,0,sinfo->hashCode);
 		  } else {
 			 tinfo = (TagInfo*)(void*)(ptrdiff_t)tag;
 			 tinfo->groupHashCode=sinfo->hashCode;
 		  }
 		  checkThreadLimits(jvmti,env, thread,sinfo);
 	  }
}

/*
 * Callback for JVMTI_THREAD_STOP
 * Note: Thread group will always be NULL, so the saved hash value is used
 *
 */
void JNICALL
cbThreadEnd(jvmtiEnv *jvmti, JNIEnv *env, jthread thread) {
	jvmtiError error;
	SessionInfo* sinfo;
	TagInfo *tinfo;
	jlong tag;
	if (gdata->vmDead || !thread) {
		return;
	}
	error = (*jvmti)->GetTag(jvmti, thread, &tag);
	check_jvmti_error(gdata->jvmti, error, "Cannot get tag");
	tinfo = (TagInfo*) (void*) (ptrdiff_t) tag;
	if (tinfo) {
		sinfo = lookupOrEnter(jvmti, tinfo->groupHashCode, NULL);
		if (sinfo) {
			sinfo->noThreads--;
		}
	}
}


/* Callback for JVMTI_EVENT_VM_OBJECT_ALLOC */
void JNICALL
cbVMObjectAlloc(jvmtiEnv *jvmti, JNIEnv *env, jthread thread,
                jobject o, jclass object_klass, jlong size)
{
	SessionInfo* sinfo;
    if ( gdata->vmDead ) {
        return;
    }
     sinfo = findSessionInfo(jvmti, env, thread,true);
    sinfo->memUsage+=size;
    tagObjectWithTagInfo(jvmti, o, sinfo,size,0);
	checkMemoryLimits(jvmti,env, thread,sinfo);
}

/* Callback for JVMTI_EVENT_OBJECT_FREE */
void JNICALL
cbObjectFree(jvmtiEnv *jvmti, jlong tag)
{
    TagInfo *tinfo;

    if ( gdata->vmDead||!tag ) {
        return;
    }

    /* The object tag is actually a pointer to a TagInfo structure */
    tinfo = (TagInfo*)(void*)(ptrdiff_t)tag;
	// Update memory usage info
	SessionInfo* sinfo;
	sinfo = lookupOrEnter(jvmti, tinfo->hashCode,NULL);
	if (sinfo) {
		sinfo->memUsage-=tinfo->size;
	}
    free(tinfo); // TODO: Can we really free the element?
}
