#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stddef.h>
#include <stdarg.h>
#include <sys/types.h>

#include "jni.h"
#include "jvmti.h"

#include "init.h"
#include "macros.h"
#include "data_utils.h"
#include "thread_utils.h"
#include "gc.h"
#include "callbacks.h"
#include "agent_util.h"

extern GlobalAgentData *gdata;

/* Creates a new jthread */
static jthread alloc_thread(JNIEnv *env) {
	jclass thrClass;
	jmethodID cid;
	jthread res;

	thrClass = (*env)->FindClass(env, "java/lang/Thread");
	if (thrClass == NULL) {
		fatal_error("Cannot find Thread class\n");
	}
	cid = (*env)->GetMethodID(env, thrClass, "<init>", "()V");
	if (cid == NULL) {
		fatal_error("Cannot find Thread constructor method\n");
	}
	res = (*env)->NewObject(env, thrClass, cid);
	if (res == NULL) {
		fatal_error("Cannot create new Thread object\n");
	}
	return res;
}

/* Callback for JVMTI_EVENT_VM_START */
void JNICALL
cbVMStart(jvmtiEnv *jvmti, JNIEnv *env) {
	enterCriticalSection(jvmti);
	{
		jclass klass;
		jfieldID field;
		jint rc;

		/* Java Native Methods for class */
		static JNINativeMethod registry[2] = { {
				STRING(RESOURCE_MANAGER_native_newobj),
				"(Ljava/lang/Object;Ljava/lang/Object;)V",
				(void*) &RESOURCE_MANAGER_native_newobj }, {
				STRING(RESOURCE_MANAGER_native_newarr),
				"(Ljava/lang/Object;Ljava/lang/Object;)V",
				(void*) &RESOURCE_MANAGER_native_newarr } };

		if (!gdata->nomem) {
			/* Register Natives for class whose methods we use */
			klass = (*env)->FindClass(env, STRING(RESOURCE_MANAGER_class));
			if (klass == NULL) {
				fatal_error("ERROR: JNI: Cannot find %s with FindClass\n",
						STRING(RESOURCE_MANAGER_class));
			}
			rc = (*env)->RegisterNatives(env, klass, registry, 2);
			if (rc != 0) {
				fatal_error(
						"ERROR: JNI: Cannot register natives for class %s\n",
						STRING(RESOURCE_MANAGER_class));
			}

			/* Engage calls. */
			field = (*env)->GetStaticFieldID(env, klass,
					STRING(RESOURCE_MANAGER_engaged), "I");
			if (field == NULL) {
				fatal_error("ERROR: JNI: Cannot get field from %s\n",
						STRING(RESOURCE_MANAGER_class));
			}
			(*env)->SetStaticIntField(env, klass, field, 1);
		}
		/* Indicate VM has started */
		gdata->vmStarted = JNI_TRUE;

	}
	exitCriticalSection(jvmti);
}

/* Callback for JVMTI_EVENT_VM_INIT */
void JNICALL
cbVMInit(jvmtiEnv *jvmti, JNIEnv *env, jthread thread) {
	jvmtiError error;
	enterCriticalSection(jvmti);
	{

		/* Indicate VM is initialized */
		gdata->vmInitialized = JNI_TRUE;
		if (!gdata->nocpu) {
			error = (*jvmti)->RunAgentThread(jvmti, alloc_thread(env), &worker,
					NULL, JVMTI_THREAD_MAX_PRIORITY);
			check_jvmti_error(jvmti, error, "running agent thread");
		}
		error = (*jvmti)->RunAgentThread(jvmti, alloc_thread(env), &gc_thread,
							NULL, JVMTI_THREAD_MAX_PRIORITY);
					check_jvmti_error(jvmti, error, "running gc thread");

	}
	exitCriticalSection(jvmti);
}

/* Callback for JVMTI_EVENT_VM_DEATH */
void JNICALL
cbVMDeath(jvmtiEnv *jvmti, JNIEnv *env) {
	jvmtiError error;

	/* Process VM Death */
	enterCriticalSection(jvmti);
	{
		jclass klass;
		jfieldID field;
		jvmtiEventCallbacks callbacks;

		/* Disengage calls in RESOURCE_MANAGER_class. */
		if (!gdata->nomem) {
			klass = (*env)->FindClass(env, STRING(RESOURCE_MANAGER_class));
			if (klass == NULL) {
				fatal_error("ERROR: JNI: Cannot find %s with FindClass\n",
						STRING(RESOURCE_MANAGER_class));
			}
			field = (*env)->GetStaticFieldID(env, klass,
					STRING(RESOURCE_MANAGER_engaged), "I");
			if (field == NULL) {
				fatal_error("ERROR: JNI: Cannot get field from %s\n",
						STRING(RESOURCE_MANAGER_class));
			}
			(*env)->SetStaticIntField(env, klass, field, 0);
		}
		/* The critical section here is important to hold back the VM death
		 *    until all other callbacks have completed.
		 */

		/* Clear out all callbacks. */
		(void) memset(&callbacks, 0, sizeof(callbacks));
		error = (*jvmti)->SetEventCallbacks(jvmti, &callbacks,
				(jint) sizeof(callbacks));
		check_jvmti_error(jvmti, error, "Cannot set jvmti callbacks");

		/* Since this critical section could be holding up other threads
		 *   in other event callbacks, we need to indicate that the VM is
		 *   dead so that the other callbacks can short circuit their work.
		 *   We don't expect an further events after VmDeath but we do need
		 *   to be careful that existing threads might be in our own agent
		 *   callback code.
		 */
		gdata->vmDead = JNI_TRUE;
		if (!gdata->nocpu) {
			(*jvmti)->RawMonitorEnter(jvmti, gdata->threadLock);
			(*jvmti)->RawMonitorNotify(jvmti, gdata->threadLock);
			(*jvmti)->RawMonitorExit(jvmti,  gdata->threadLock);
		}
		(*jvmti)->RawMonitorEnter(jvmti, gdata->gcLock);
		(*jvmti)->RawMonitorNotify(jvmti, gdata->gcLock);
		(*jvmti)->RawMonitorExit(jvmti, gdata->gcLock);
	}
	exitCriticalSection(jvmti);
	log_message("---Log ended---");
}
