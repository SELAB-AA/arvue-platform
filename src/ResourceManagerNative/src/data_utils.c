#include <time.h>
#include "data_utils.h"
#include "macros.h"
#include "agent_util.h"

extern GlobalAgentData *gdata;
/* Allocate new SessionInfo */
SessionInfo *
newSessionInfo(unsigned int index, jint hashCode, const char* sessionId) {
	SessionInfo *sinfo;
	sinfo = (SessionInfo*) calloc(1, sizeof(SessionInfo));
	if (sinfo == NULL) {
		fatal_error("ERROR: Ran out of malloc() space\n");
	}
	/* Copy session name and hashCode */
	sinfo->sessionId = strdup(sessionId);
	sinfo->hashCode = hashCode;
	time(&sinfo->timestamp);
	// Insert as the head
	if (gdata->sessionsHead[index]) {
		gdata->sessionsHead[index]->prev = sinfo;
		sinfo->next = gdata->sessionsHead[index];
		gdata->sessionsHead[index] = sinfo;
	} else {
		gdata->sessionsHead[index] = sinfo;
	}
	gdata->info_count++;
	return sinfo;
}

/* Lookup or create a new SessionInfo */
/* If sessionId is NULL, no new SessionInfo item is created */
SessionInfo *
lookupOrEnter(jvmtiEnv *jvmti, jint hashCode, const char* sessionId) {
	SessionInfo* sinfo = NULL;
	// Get hash index from the middle hashCode. In this way also pointers may be used as a hashCode
	// 0x000FFF00
	unsigned int index = ((hashCode & (((1 << HASH_SIZE) - 1) << 8)) >> 8);
	SessionInfo* info = gdata->sessionsHead[index];
	if (!info && !sessionId) {
		return NULL;
	}
	enterCriticalSection(jvmti);
	{

		/* TODO: Optimize this using binary search or similar */
		while (info) {
			if (info->hashCode == hashCode) {
				sinfo = info;
				break;
			}
			info = info->next;
		}
		/* If we didn't find anything we need to enter a new entry */
		if (sinfo == NULL) {
			if (!sessionId) { // Do not create a new entry, return NULL
				exitCriticalSection(jvmti);
				return NULL;
			}

			/* Create new hash table element */
			sinfo = newSessionInfo(index, hashCode, sessionId);
			sinfo->limits = getLimits(sessionId);
			sinfo->index = index;
		} else { // Move to first, so recently used items are easier to access
			// TODO: Does this really help?
			if (sinfo != gdata->sessionsHead[index]) {
				SessionInfo* next = sinfo->next;
				SessionInfo* prev = sinfo->prev;
				gdata->sessionsHead[index]->prev = sinfo;
				sinfo->next = gdata->sessionsHead[index];
				sinfo->prev = NULL;
				gdata->sessionsHead[index] = sinfo;
				if (next)
					next->prev = prev;
				if (prev)
					prev->next = next;
			}
		}
	}
	exitCriticalSection(jvmti);

	return sinfo;
}

/* Get SessionInfo for this allocation */
SessionInfo *
findSessionInfo(jvmtiEnv *jvmti, JNIEnv *env, jthread thread, bool createnew) {
	SessionInfo *sinfo;
	jvmtiError error;
	jint hashCode;
	sinfo = NULL;
	if (thread != NULL) {
		/* Lookup this entry */
		jvmtiThreadInfo threadInfo;
		jvmtiThreadGroupInfo groupInfo;
		error = (*jvmti)->GetThreadInfo(jvmti, thread, &threadInfo);
		if (error == JVMTI_ERROR_WRONG_PHASE) {
			return NULL;
		}
		check_jvmti_error(jvmti, error, "Cannot get thread info");
		deallocate(jvmti, threadInfo.name);
		(*env)->DeleteLocalRef(env, threadInfo.context_class_loader);

		if (!threadInfo.thread_group) {
			debug_message("\nFind: thread group was NULL\n");
			return NULL;
		}

		error = (*jvmti)->GetObjectHashCode(jvmti, threadInfo.thread_group,
				&hashCode);
		check_jvmti_error(jvmti, error, "Cannot get thread group hashCode");
		if (createnew) {
			error = (*jvmti)->GetThreadGroupInfo(jvmti,
					threadInfo.thread_group, &groupInfo);
			check_jvmti_error(jvmti, error, "Cannot get thread group info");
		}

		sinfo = lookupOrEnter(jvmti, hashCode,
				createnew ? groupInfo.name : NULL);
		if (createnew) {
			(*env)->DeleteLocalRef(env, groupInfo.parent);
			deallocate(jvmti, groupInfo.name);
		}
		(*env)->DeleteLocalRef(env, threadInfo.thread_group);
	}
	return sinfo;
}

/* Removes a session info from the hash table */
void freeSessionInfo(SessionInfo* info) {
	if (!info)
		return;
	free(info->sessionId);
	if (info->prev) {
		info->prev->next = info->next;
	} else {
		gdata->sessionsHead[info->index] = info->next;
	}
	if (info->next) {
		info->next->prev = info->prev;
	}
	free(info);
	gdata->info_count--;
}

/* Tag an object with a TagInfo pointer. */
void tagObjectWithTagInfo(jvmtiEnv *jvmti, jobject object, SessionInfo *sinfo,
		jlong size, jint groupcode) {
	jvmtiError error;
	jlong tag;
	TagInfo* tinfo = (TagInfo*) calloc(1, sizeof(TagInfo));

	tinfo->hashCode = sinfo->hashCode;
	tinfo->size = size;

	tinfo->groupHashCode = groupcode;

	/* Tag this object with this TagInfo pointer */
	tag = (jlong) (ptrdiff_t) (void*) tinfo;
	error = (*jvmti)->SetTag(jvmti, object, tag);
	check_jvmti_error(jvmti, error, "Cannot tag object");
}

/* Enter a critical section by doing a JVMTI Raw Monitor Enter */
void enterCriticalSection(jvmtiEnv *jvmti) {
	jvmtiError error;
	error = (*jvmti)->RawMonitorEnter(jvmti, gdata->lock);
	check_jvmti_error(jvmti, error, "Cannot enter with raw monitor");
}

/* Exit a critical section by doing a JVMTI Raw Monitor Exit */
void exitCriticalSection(jvmtiEnv *jvmti) {
	jvmtiError error;
	error = (*jvmti)->RawMonitorExit(jvmti, gdata->lock);
	check_jvmti_error(jvmti, error, "Cannot exit with raw monitor");
}
