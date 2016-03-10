#include "data_utils.h"
#include "thread_utils.h"
#include "agent_util.h"
#include "resource_handlers.h"
#include <sys/time.h>
extern  GlobalAgentData *gdata;


char* getThreadName(jvmtiEnv *jvmti, jthread thread)
{
	jvmtiError error;
	jvmtiThreadInfo threadInfo;
	error = (*jvmti)->GetThreadInfo(jvmti,thread,&threadInfo);
	if (error!=JVMTI_ERROR_NONE)
		return NULL;
	return threadInfo.name;
}

static void
calculateCPUTimes(JNIEnv* jni)
{
	jvmtiError error;
	jint count,i;
	jthread* threads;
	jlong cputime;
	error=(*(gdata->jvmti))->GetAllThreads(gdata->jvmti,&count,&threads);
	check_jvmti_error(gdata->jvmti, error, "get all threads");
	for (i=0;i<count;++i) {
		error=(*(gdata->jvmti))->GetThreadCpuTime(gdata->jvmti,threads[i],&cputime);
		if (error==JVMTI_ERROR_NONE) {
			SessionInfo* sinfo;
			TagInfo* tinfo;
			jlong tag;
			error = (*(gdata->jvmti))->GetTag(gdata->jvmti, threads[i], &tag);
			if (error==JVMTI_ERROR_NONE) {
				tinfo = (TagInfo*) (void*) (ptrdiff_t) tag;
				if (tinfo) {
					sinfo = lookupOrEnter(gdata->jvmti, tinfo->groupHashCode, NULL);
					if (sinfo) {
						sinfo->cpuUsage += (cputime - tinfo->cputime);
						tinfo->cputime = cputime;
						checkCPULimits(gdata->jvmti,jni, threads[i],cputime, sinfo);
					}
				}
			}
		}
	}

	deallocate(gdata->jvmti,threads);
}

void JNICALL
worker(jvmtiEnv* jvmti, JNIEnv* jni, void *p) {
	jvmtiError err;

	stdout_message("CPUTime worker started...\n");

	while (!gdata->vmDead) {
		err = (*jvmti)->RawMonitorEnter(jvmti, gdata->threadLock);
		check_jvmti_error(jvmti, err, "raw monitor enter");

		// Wait
		err = (*jvmti)->RawMonitorWait(jvmti, gdata->threadLock, 500);

		if (!gdata->vmDead && err == JVMTI_ERROR_NONE) {
			calculateCPUTimes(jni);
		}
		err = (*jvmti)->RawMonitorExit(jvmti, gdata->threadLock);
		check_jvmti_error(jvmti, err, "raw monitor exit");

	}

     stdout_message("CPUTime worker exit...\n");
 }

