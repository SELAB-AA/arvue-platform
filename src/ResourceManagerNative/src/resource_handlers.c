
#include "resource_handlers.h"
#include "thread_utils.h"
#include "agent_util.h"
#include "thread_utils.h"

extern GlobalAgentData *gdata;

// TODO: Find a better way to end an application!

static
void stopThread(jvmtiEnv *jvmti, JNIEnv* env, jthread thread,
		SessionInfo *sinfo, const char* reason) {

	jvmtiError error;
	static jthread stoppingit = NULL;
	/*q
	 * If we are already stopping a thread, return.
	 * NewObject will need some memory and if we are in the middle of stopping
	 * thread because of memorylimit, we won't get any exception object at all!
	 * Note: In this way, there is a (small) possibility that we won't stop some
	 * other thread.
	 *
	 */
	if (stoppingit || !thread)
		return;
	sinfo->interrupts++;
	stoppingit = thread;
	char *name = getThreadName(jvmti, thread);
	log_message("Limits exceeded:%s\t%s\t%s",sinfo->sessionId,name?name:"<unknown>",reason);

	if (sinfo->limits->maxInterrupts!=-1 && sinfo->interrupts > sinfo->limits->maxInterrupts) {
		stdout_message("Session %s was interrupted %u times!\n",
				sinfo->sessionId, sinfo->interrupts);
			if (name) {
				stdout_message("\n%s:Stopping thread %s\n", reason, name);
				deallocate(jvmti, name);
				name=NULL;
			}
			jclass newExcCls;
			newExcCls = (*env)->FindClass(env, "java/lang/RuntimeException");

			if (newExcCls) {
				jmethodID id = (*env)->GetMethodID(env, newExcCls, "<init>", "()V");
				jobject excObj = (*env)->NewObject(env, newExcCls, id);
				if (excObj) {
					error = (*jvmti)->StopThread(jvmti, thread, excObj);
					check_jvmti_error(jvmti, error, "Cannot stop thread");
				}
				(*env)->DeleteLocalRef(env, newExcCls);
				stoppingit = NULL;
				return;

			}
	}
	if (name) {
		stdout_message("\n%s:Interrupting thread %s\n", reason, name);
		deallocate(jvmti, name);
	}
	error = (*jvmti)->InterruptThread(jvmti, thread);
	check_jvmti_error(jvmti, error, "Cannot interrupt thread");
	// Throw also an exception
	/* if (newExcCls != NULL) {
	 (*env)->ThrowNew(env, newExcCls, "Limits");
	(*env)->DeleteLocalRef(env, newExcCls);
	 } */
	stoppingit = NULL;
}

/* Check if memory consumption exceeds the one set in sinfo */
void
checkMemoryLimits(jvmtiEnv *jvmti,  JNIEnv* env, jthread thread, SessionInfo *sinfo)
{
#ifdef DEBUG_INFO
	if (strncmp(sinfo->sessionId, "Vaadin Application ThreadGroup", 30) == 0)
		stdout_message("Memory usage: %s %ld \r", sinfo->sessionId + 33,
				sinfo->memUsage);
#endif
	if (sinfo->limits->memUsageLimit!=-1&&sinfo->memUsage > sinfo->limits->memUsageLimit) {
		stopThread(jvmti,env, thread,sinfo,"Memory");
	}
}

void
checkThreadLimits(jvmtiEnv *jvmti, JNIEnv* env, jthread thread,SessionInfo *sinfo)
{
#ifdef DEBUG_INFO
	if (strncmp(sinfo->sessionId, "Vaadin Application ThreadGroup", 30) == 0)
		stdout_message("Thread usage: %s %ld \r", sinfo->sessionId + 33,
				sinfo->noThreads);
#endif
	if (sinfo->limits->noThreadsLimit!=-1&&sinfo->noThreads > sinfo->limits->noThreadsLimit) {
		stopThread(jvmti,env, thread,sinfo,"Thread");
	}

}

void
checkCPULimits(jvmtiEnv *jvmti,  JNIEnv* env, jthread thread, long long threadTime, SessionInfo* sinfo)
{
#ifdef DEBUG_INFO
	if (strncmp(sinfo->sessionId, "Vaadin Application ThreadGroup", 30) == 0)
		stdout_message("\n****ThreadTime:%s %.2f \n",sinfo->sessionId,(float)(sinfo->cpuUsage/1000000000.0));
#endif
	if ((sinfo->limits->cpuUsageLimit!=-1		&&	sinfo->cpuUsage > sinfo->limits->cpuUsageLimit) ||
		(sinfo->limits->cpuThreadUsageLimit!=-1	&&	threadTime > sinfo->limits->cpuThreadUsageLimit)) {
		stopThread(jvmti,env, thread,sinfo, "CPUTime");
	}

}
