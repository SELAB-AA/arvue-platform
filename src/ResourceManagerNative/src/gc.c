#include "data_utils.h"
#include "agent_util.h"
#include "macros.h"
#include "gc.h"

extern  GlobalAgentData *gdata;

static int cmp(const void *a, const void* b)
{
	const jint *ia=(const jint*)a;
	const jint *ib=(const jint*)b;
	return *ia-*ib;
}

static int binarySearch(jint sortedArray[], int first, int last, jint key) {
   while (first <= last) {
       int mid = (first + last) / 2;  // compute mid point.
       if (key > sortedArray[mid])
           first = mid + 1;  // repeat search in top half.
       else if (key < sortedArray[mid])
           last = mid - 1; // repeat search in bottom half.
       else
           return mid;     // found it. return position /////
   }
   return -1;    // failed to find key
}

/* Check all session infos and remove all that do not have existing thread group */
static void handlegc(jvmtiEnv* jvmti, jint* hashcodes, jint group_count) {
	int i;
	qsort(hashcodes, group_count, sizeof(jint), cmp);
	enterCriticalSection(jvmti);
	{
		for (i = 0; i < (1 << HASH_SIZE); ++i) {
			SessionInfo* ptr = gdata->sessionsHead[i];
			while (ptr) {
				SessionInfo* c = ptr;
				ptr = ptr->next;
				if (binarySearch(hashcodes, 0, group_count - 1, c->hashCode)
						== -1) {
					freeSessionInfo(c);
				}
			}
		}
	}
	exitCriticalSection(jvmti);

}
/* Get hash codes (recursively) from all thread groups in the system */
static void handlehash(jvmtiEnv* jvmti, jint* hashcodes, jthreadGroup* groups, jint group_count, jint* max_elements, jint *total) {
	jvmtiError error;
	jint i;

	/* Do we have enough room? */
	if (*max_elements<*total+group_count) {
		*max_elements=*total+group_count*4;
		hashcodes=(jint*)realloc(hashcodes,*max_elements*sizeof(jint));
		if (hashcodes == NULL) {
				fatal_error("ERROR: Ran out of malloc() space\n");
		}
	}
	/* Get hash codes */
	for (i = 0; i < group_count; i++) {
		error = (*jvmti)->GetObjectHashCode(jvmti, groups[i], &hashcodes[i+(*total)]);
		if (error != JVMTI_ERROR_NONE)
			break;
	}
	*total+=group_count; // Add total counter
	/* Get children */
	for (i=0;i<group_count;i++) {
		jint thread_count;
		jthread* threads;
		jint child_count;
		jthreadGroup* child_groups;
		error=(*jvmti)->GetThreadGroupChildren(jvmti,groups[i],&thread_count,&threads,&child_count,&child_groups);
		if (error == JVMTI_ERROR_NONE) {
			deallocate(jvmti,threads); // We don't need thread information
			// handle children
			if (child_count>0)
				handlehash(jvmti,hashcodes,child_groups,child_count,max_elements,total);
			deallocate(jvmti,child_groups);
		}
	}

}

/* Run garbage collection */
static void rungc(jvmtiEnv* jvmti) {
	jvmtiError error;
	jint group_count;
	jint* hashcodes;
	jthreadGroup* groups;
	jint max_elements;
	jint total;
	debug_message("Running GC...\n");
	// Get all the information and check if the groups still exist
	// Remove the ones that are obsolete
	error = (*jvmti)->GetTopThreadGroups(jvmti, &group_count, &groups);
	if (error != JVMTI_ERROR_NONE)
		return;
	total=0;
	max_elements=gdata->info_count;
	hashcodes = (jint*) malloc(max_elements*sizeof(jint));
	if (hashcodes == NULL) {
			fatal_error("ERROR: Ran out of malloc() space\n");
	}
	/* Collect all hash codes...*/
	handlehash(jvmti,hashcodes,groups,group_count,&max_elements, &total);
	deallocate(jvmti, groups);
	/* ... and remove information */
	handlegc(jvmti,hashcodes,total);
	free(hashcodes);
	debug_message("GC done...\n");

}

void JNICALL
gc_thread(jvmtiEnv* jvmti, JNIEnv* jni, void *p) {

	jvmtiError err;

	stdout_message("GC thread started...\n");

	while (!gdata->vmDead) {
		err = (*jvmti)->RawMonitorEnter(jvmti, gdata->gcLock);
			check_jvmti_error(jvmti, err, "raw monitor enter");
			// Wait for five minutes
			err = (*jvmti)->RawMonitorWait(jvmti, gdata->gcLock, 5 * 60 * 1000);

			if (!gdata->vmDead && err == JVMTI_ERROR_NONE) {
				rungc(jvmti);
			}
			err = (*jvmti)->RawMonitorExit(jvmti, gdata->gcLock);
			check_jvmti_error(jvmti, err, "gc raw monitor exit");

	}
	  stdout_message("GC thread exit...\n");
}

