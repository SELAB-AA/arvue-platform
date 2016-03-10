
#include "info_interface.h"
#include "data_utils.h"
#include "macros.h"
#include "agent_util.h"

extern  GlobalAgentData *gdata;
/*
 *
public class ResourceInfo {
	public String sessionId;
	public long memUsage;
	public long cpuUsage;
	public int noThreads;
	public int interrupts;
	public long memUsageLimit;
	public long cpuUsageLimit;
	public int noThreadsLimit;
	public int maxInterrupts;

	public native void update(ThreadGroup group);
}
 *
 */

#define SET_VALUE(name,setter,sig) \
	jfieldID name=(*env)->GetFieldID(env,c,STRING(name),sig); \
	if (name) {\
		(*env)->setter(env,defaultObj,name,sinfo->name); \
	}

#define SET_LIMIT_VALUE(name,setter,sig) \
	jfieldID name=(*env)->GetFieldID(env,c,STRING(name),sig); \
	if (name) {\
		(*env)->setter(env,defaultObj,name,sinfo->limits->name); \
	}


static void updateInfoObject(JNIEnv *env, jobject defaultObj, SessionInfo* sinfo)
{
	if (!sinfo) {
		stdout_message("updateInfoObject:NULL sinfo\n");
		// TODO: throw an exception
	}
	jclass c = (*env)->GetObjectClass(env, defaultObj);

	jfieldID sessionId=(*env)->GetFieldID(env, c, "sessionId", "Ljava/lang/String;");
	if (sessionId) {
		(*env)->SetObjectField(env,defaultObj,sessionId, (*env)->NewStringUTF(env, sinfo->sessionId));
	}
	jfieldID dateId=(*env)->GetFieldID(env,c,"timestamp","Ljava/lang/String;");
	if (dateId) {
		(*env)->SetObjectField(env,defaultObj,dateId, (*env)->NewStringUTF(env, asctime(localtime(&(sinfo->timestamp)))));
	}

	SET_VALUE(memUsage,SetLongField,"J")
	SET_VALUE(cpuUsage,SetLongField,"J")
	SET_VALUE(noThreads,SetIntField,"I")
	SET_VALUE(interrupts,SetIntField,"I")

	SET_LIMIT_VALUE(memUsageLimit,SetLongField,"J")
	SET_LIMIT_VALUE(cpuUsageLimit,SetLongField,"J")
	SET_LIMIT_VALUE(cpuThreadUsageLimit,SetLongField,"J")
	SET_LIMIT_VALUE(noThreadsLimit,SetIntField,"I")
	SET_LIMIT_VALUE(maxInterrupts,SetIntField,"I")
	(*env)->DeleteLocalRef(env,c);
}

JNIEXPORT void JNICALL Java_fi_tut_cloud_arvue_resource_ResourceInfo_update(JNIEnv *env, jobject defaultObj, jobject threadgroup)
{
    jint hashCode;
    SessionInfo *sinfo;
    jvmtiError error;

	error = (*(gdata->jvmti))->GetObjectHashCode(gdata->jvmti,threadgroup,&hashCode);
	check_jvmti_error(gdata->jvmti, error, "Interface:Cannot get thread group hashCode");
	sinfo = lookupOrEnter(gdata->jvmti, hashCode, NULL);
	updateInfoObject(env,defaultObj,sinfo);
}

JNIEXPORT jobjectArray JNICALL Java_fi_tut_cloud_arvue_resource_ResourceInfo_getAll(JNIEnv *env, jclass klass)
{
	int k;
	jsize i;
	jobject object;
	jobjectArray result=(*env)->NewObjectArray(env,gdata->info_count,klass,NULL);
	if (result) {
		enterCriticalSection(gdata->jvmti);
		{
			jmethodID id = (*env)->GetMethodID(env, klass, "<init>", "()V");
			for (i = 0, k = 0; k < (1 << HASH_SIZE); ++k) {
				SessionInfo* ptr = gdata->sessionsHead[k];
				while (ptr) {
					object = (*env)->NewObject(env, klass, id);
					updateInfoObject(env, object, ptr);
					(*env)->SetObjectArrayElement(env, result, i, object);
					++i;
					ptr = ptr->next;
				}
			}
		}
		exitCriticalSection(gdata->jvmti);
	}
	return result;
}

JNIEXPORT void JNICALL Java_fi_tut_cloud_arvue_resource_ResourceInfo_gc(JNIEnv *env, jclass cls)
{
	  (*(gdata->jvmti))->RawMonitorEnter(gdata->jvmti, gdata->gcLock);
	  (*(gdata->jvmti))->RawMonitorNotify(gdata->jvmti, gdata->gcLock);
	  (*(gdata->jvmti))->RawMonitorExit(gdata->jvmti, gdata->gcLock);
}
