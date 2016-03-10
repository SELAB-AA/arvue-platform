#include "resource_limits.h"
#include "data_utils.h"
#include "agent_util.h"
#include "macros.h"

/* Gets resource limits for the specific thread group */

extern GlobalAgentData *gdata;

const LimitInfo*
getLimits(const char* sessionCode)
{
//	static const LimitInfo vaadin={
//			100000000L,// jlong memUsageLimit
//			15*60*1000000000LL,// jlong cpuUsageLimit (-1=no limits)
//			15*1000000000LL,// jlong cpuThreadUsageLimit
//			20,// jint noThreadsLimit
//			5 // jint maxInterrupts
//	};

	static const LimitInfo nolimits={
			-1,-1,-1,-1,-1
	};

	if (!gdata->nolimits && sessionCode) {

		LimitInfoEx* ptr = gdata->limitInfos;
		while (ptr) {
			if (strstr(sessionCode, ptr->pattern)) {
				return &(ptr->info);
			}
			ptr=ptr->next;
		}
	}
//
//	if (sessionCode&&(strncmp(sessionCode, "Vaadin Application ThreadGroup", 30) == 0))
//		return &vaadin;
	return &nolimits;
}
#define BUFFER_SIZE 1024
void loadLimits(const char* filename)
{
	FILE* file=fopen(filename,"r");
	char buffer[BUFFER_SIZE];
	float cpu,thread;
	long memory;
	if (!file) {
		stdout_message("Cannot open limit file %s\n",filename);
		return;
	}
	while (fgets(buffer, BUFFER_SIZE, file) != NULL) {
		LimitInfoEx* info = (LimitInfoEx*) calloc(1, sizeof(LimitInfoEx));
		if (info == NULL) {
			fclose(file);
			fatal_error("ERROR: Ran out of malloc() space\n");
		}
		if (buffer[0] == '#' || buffer[0]=='\n')
			continue;
		buffer[strlen(buffer)-1]=0;
		info->pattern = strdup(buffer);
		if (4 == fscanf(file, "%ld %f %f %d %d", &memory,
				&cpu,
				&thread,
				&(info->info.noThreadsLimit), &(info->info.maxInterrupts))) {

			info->info.memUsageLimit=memory*1024*1024;
			info->info.cpuUsageLimit=cpu*1000000000LL;
			info->info.cpuThreadUsageLimit=thread*1000000000LL;
			info->next = gdata->limitInfos;
			gdata->limitInfos = info;
			debug_message("Limits:%s %lld %lld %lld %d %d\n",info->pattern,info->info.memUsageLimit,info->info.cpuUsageLimit,info->info.cpuThreadUsageLimit,info->info.noThreadsLimit,info->info.maxInterrupts);
		} else {
			debug_message("Error in input!\n");
		}
	}
	fclose(file);
}
