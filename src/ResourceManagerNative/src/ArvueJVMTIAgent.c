/*
 * Arvue Resource Manager Agent
 *
 * Part of the code is Copyright (c) 2004, 2006, Oracle and/or its affiliates. All rights reserved.
 *
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stddef.h>
#include <stdarg.h>

/* General JVM/Java functions, types and macros. */

#include <sys/types.h>


#include "ArvueJVMTIAgent.h"
#include "java_crw_demo.h"


#include "jni.h"
#include "jvmti.h"


#include "agent_util.h"
#include "init.h"
#include "callbacks.h"
#include "macros.h"

#include "resource_handlers.h"
/* -------------------------------------------------------------------
 * Some constant names that tie to Java class/method names.
 *    We assume the Java class whose static methods we will be calling
 *    looks like:
 *
 * public class ResourceManager {
 *     private static int engaged;
 *     private static native void _newobj(Object thr, Object o);
 *     public static void newobj(Object o)
 *     {
 *              if ( engaged != 0 ) {
 *               _newobj(Thread.currentThread(), o);
 *           }
 *     }
 *     private static native void _newarr(Object thr, Object a);
 *     public static void newarr(Object a)
 *     {
 *            if ( engaged != 0 ) {
 *               _newarr(Thread.currentThread(), a);
 *           }
 *     }
 * }
 *
 *    The engaged field allows us to inject all classes (even system classes)
 *    and delay the actual calls to the native code until the VM has reached
 *    a safe time to call native methods (Past the JVMTI VM_START event).
 *
 */


/* ------------------------------------------------------------------- */

 GlobalAgentData *gdata;


/* Callback for JVMTI_EVENT_CLASS_FILE_LOAD_HOOK */
static void JNICALL
cbClassFileLoadHook(jvmtiEnv *jvmti, JNIEnv* env,
                jclass class_being_redefined, jobject loader,
                const char* name, jobject protection_domain,
                jint class_data_len, const unsigned char* class_data,
                jint* new_class_data_len, unsigned char** new_class_data)
{
    enterCriticalSection(jvmti); {
        /* It's possible we get here right after VmDeath event, be careful */
        if ( !gdata->vmDead ) {

            const char * classname;

            /* Name can be NULL, make sure we avoid SEGV's */
            if ( name == NULL ) {
                classname = java_crw_demo_classname(class_data, class_data_len,
                                NULL);
                if ( classname == NULL ) {
                    fatal_error("ERROR: No classname in classfile\n");
                }
            } else {
                classname = strdup(name);
                if ( classname == NULL ) {
                    fatal_error("ERROR: Ran out of malloc() space\n");
                }
            }

            *new_class_data_len = 0;
            *new_class_data     = NULL;

            /* The tracker class itself? */
            if ( strcmp(classname, STRING(RESOURCE_MANAGER_class)) != 0 ) {
                jint           cnum;
                int            systemClass;
                unsigned char *newImage;
                long           newLength;

                /* Get number for every class file image loaded */
                cnum = gdata->ccount++;

                /* Is it a system class? If the class load is before VmStart
                 *   then we will consider it a system class that should
                 *   be treated carefully. (See java_crw_demo)
                 */
                systemClass = 0;
                if ( !gdata->vmStarted ) {
                    systemClass = 1;
                }

                newImage = NULL;
                newLength = 0;

                /* Call the class file reader/write demo code */
                java_crw_demo(cnum,
                    classname,
                    class_data,
                    class_data_len,
                    systemClass,
                    STRING(RESOURCE_MANAGER_class),
                    "L" STRING(RESOURCE_MANAGER_class) ";",
                    NULL, NULL,
                    NULL, NULL,
                    STRING(RESOURCE_MANAGER_newobj), "(Ljava/lang/Object;)V",
                    STRING(RESOURCE_MANAGER_newarr), "(Ljava/lang/Object;)V",
                    &newImage,
                    &newLength,
                    NULL,
                    NULL);

                /* If we got back a new class image, return it back as "the"
                 *   new class image. This must be JVMTI Allocate space.
                 */
                if ( newLength > 0 ) {
                    unsigned char *jvmti_space;
                    jvmti_space = (unsigned char *)allocate(jvmti, (jint)newLength);
                    (void)memcpy((void*)jvmti_space, (void*)newImage, (int)newLength);
                    *new_class_data_len = (jint)newLength;
                    *new_class_data     = jvmti_space; /* VM will deallocate */
                }

                /* Always free up the space we get from java_crw_demo() */
                if ( newImage != NULL ) {
                    (void)free((void*)newImage); /* Free malloc() space with free() */
                }
            }

            (void)free((void*)classname);
        }
    } exitCriticalSection(jvmti);
}

/* Parse the options for this heapTracker agent */
static void
parse_agent_options(char *options)
{
    #define MAX_TOKEN_LENGTH        16
    char  token[MAX_TOKEN_LENGTH];
    char *next;

    /* Defaults */

    /* Parse options and set flags in gdata */
    if ( options==NULL ) {
        return;
    }

    /* Get the first token from the options string. */
    next = get_token(options, ",=", token, (int)sizeof(token));

    /* While not at the end of the options string, process this option. */
    while ( next != NULL ) {
        if ( strcmp(token,"help")==0 ) {
            stdout_message("The Arvue Resource Manager JVMTI agent\n");
            stdout_message("\n");
            stdout_message(" java -agent:ArvueResourceManager[=options] ...\n");
            stdout_message("\n");
            stdout_message("The options are comma separated:\n");
            stdout_message("\t help\t\t\tPrint help information\n");
            stdout_message("\t nomem\t\t\tNo memory information is collected\n");
            stdout_message("\t nocpu\t\t\tNo CPU usage information is collected\n");
            stdout_message("\t nothread\t\tNo thread information is collected\n");
            stdout_message("\t nolimits\t\tNo limits are checked\n");
            stdout_message("\t limitfile=<file>\tLoad limit information from a <file>\n");
            stdout_message("\t logfile=<file>\tStore limit violations to a <file>\n");
            stdout_message("\n");
            exit(0);
        } else if ( strcmp(token,"nomem")==0 ) {
        	gdata->nomem=1;
        } else if ( strcmp(token,"nocpu")==0 ) {
        	gdata->nocpu=1;
        } else if ( strcmp(token,"nolimits")==0 ) {
        	gdata->nolimits=1;
        } else if ( strcmp(token,"nothread")==0 ) {
        	gdata->nothreads=1;
        } else if ( strcmp(token,"limitfile")==0 ) {
        	if (gdata->nolimits) {
        		stdout_message("**Warning:nolimits option has already been selected\n");
        	}
                    next = get_token(next, ",=", gdata->limitfile, (int)sizeof(gdata->limitfile));
                    if ( next == NULL ) {
                        fatal_error("ERROR: Cannot parse limitfile=<file>: %s\n", options);
                    }
                    stdout_message("Using limit file '%s'\n",gdata->limitfile);
                    loadLimits(gdata->limitfile);
        } else if ( strcmp(token,"logfile")==0 ) {
                	if (gdata->nolimits) {
                		stdout_message("**Warning:nolimits option has already been selected\n");
                	}
                            next = get_token(next, ",=", gdata->logfile, (int)sizeof(gdata->logfile));
                            if ( next == NULL ) {
                                fatal_error("ERROR: Cannot parse logfile=<file>: %s\n", options);
                            }
                            stdout_message("Using log file '%s'\n",gdata->logfile);
                            log_message("---Log started---");
        } else if ( token[0]!=0 ) {
            /* We got a non-empty token and we don't know what it is. */
            fatal_error("ERROR: Unknown option: %s\n", token);
        }
        /* Get the next token (returns NULL if there are no more) */
        next = get_token(next, ",=", token, (int)sizeof(token));
    }
}

/* Agent_OnLoad: This is called immediately after the shared library is
 *   loaded. This is the first code executed.
 */
JNIEXPORT jint JNICALL
Agent_OnLoad(JavaVM *vm, char *options, void *reserved)
{
    static GlobalAgentData data;
    jvmtiEnv              *jvmti;
    jvmtiError             error;
    jint                   res;
    jvmtiCapabilities      capabilities;
    jvmtiEventCallbacks    callbacks;

    /* Setup initial global agent data area
     *   Use of static/extern data should be handled carefully here.
     *   We need to make sure that we are able to cleanup after ourselves
     *     so anything allocated in this library needs to be freed in
     *     the Agent_OnUnload() function.
     */
    (void)memset((void*)&data, 0, sizeof(data));
    gdata = &data;

    /* First thing we need to do is get the jvmtiEnv* or JVMTI environment */
    res = (*vm)->GetEnv(vm, (void **)&jvmti, JVMTI_VERSION_1);
    if (res != JNI_OK) {
        /* This means that the VM was unable to obtain this version of the
         *   JVMTI interface, this is a fatal error.
         */
        fatal_error("ERROR: Unable to access JVMTI Version 1 (0x%x),"
                " is your JDK a 5.0 or newer version?"
                " JNIEnv's GetEnv() returned %d\n",
               JVMTI_VERSION_1, res);
    }

    /* Here we save the jvmtiEnv* for Agent_OnUnload(). */
    gdata->jvmti = jvmti;

    /* Parse any options supplied on java command line */
    parse_agent_options(options);

    /* Immediately after getting the jvmtiEnv* we need to ask for the
     *   capabilities this agent will need.
     */
    (void)memset(&capabilities,0, sizeof(capabilities));
    (void)memset(&callbacks,0, sizeof(callbacks));

    capabilities.can_tag_objects  = 1;
    if (!gdata->nomem) {
    	capabilities.can_generate_object_free_events  = 1;
    	capabilities.can_generate_vm_object_alloc_events  = 1;
        capabilities.can_generate_all_class_hook_events = 1;
        /* JVMTI_EVENT_OBJECT_FREE */
        callbacks.ObjectFree        = &cbObjectFree;
        /* JVMTI_EVENT_VM_OBJECT_ALLOC */
        callbacks.VMObjectAlloc     = &cbVMObjectAlloc;
        /* JVMTI_EVENT_CLASS_FILE_LOAD_HOOK */
        callbacks.ClassFileLoadHook = &cbClassFileLoadHook;

    }
    if (!gdata->nolimits) {
    	capabilities.can_signal_thread = 1;
    }
    if (!gdata->nocpu) {
    	capabilities.can_get_thread_cpu_time=1;
    }
    if (!gdata->nothreads) {
        /* JVMTI_EVENT_THREAD_START */
        callbacks.ThreadStart     = &cbThreadStart;
        /* JVMTI_EVENT_THREAD_STOP */
        callbacks.ThreadEnd    = &cbThreadEnd;
    }
    error = (*jvmti)->AddCapabilities(jvmti, &capabilities);
    check_jvmti_error(jvmti, error, "Unable to get necessary JVMTI capabilities.");

    /* JVMTI_EVENT_VM_START */
    callbacks.VMStart           = &cbVMStart;
    /* JVMTI_EVENT_VM_INIT */
    callbacks.VMInit            = &cbVMInit;
    /* JVMTI_EVENT_VM_DEATH */
    callbacks.VMDeath           = &cbVMDeath;


    error = (*jvmti)->SetEventCallbacks(jvmti, &callbacks, (jint)sizeof(callbacks));
    check_jvmti_error(jvmti, error, "Cannot set jvmti callbacks");

    /* At first the only initial events we are interested in are VM
     *   initialization, VM death, and Class File Loads.
     *   Once the VM is initialized we will request more events.
     */
    error = (*jvmti)->SetEventNotificationMode(jvmti, JVMTI_ENABLE,
                          JVMTI_EVENT_VM_START, (jthread)NULL);
    check_jvmti_error(jvmti, error, "Cannot set event notification");
    error = (*jvmti)->SetEventNotificationMode(jvmti, JVMTI_ENABLE,
                          JVMTI_EVENT_VM_INIT, (jthread)NULL);
    check_jvmti_error(jvmti, error, "Cannot set event notification");
    error = (*jvmti)->SetEventNotificationMode(jvmti, JVMTI_ENABLE,
                          JVMTI_EVENT_VM_DEATH, (jthread)NULL);
    check_jvmti_error(jvmti, error, "Cannot set event notification");
    if (!gdata->nomem) {
		error = (*jvmti)->SetEventNotificationMode(jvmti, JVMTI_ENABLE,
				JVMTI_EVENT_OBJECT_FREE, (jthread) NULL);
		check_jvmti_error(jvmti, error, "Cannot set event notification");
		error = (*jvmti)->SetEventNotificationMode(jvmti, JVMTI_ENABLE,
				JVMTI_EVENT_VM_OBJECT_ALLOC, (jthread) NULL);
		check_jvmti_error(jvmti, error, "Cannot set event notification");
		error = (*jvmti)->SetEventNotificationMode(jvmti, JVMTI_ENABLE,
				JVMTI_EVENT_CLASS_FILE_LOAD_HOOK, (jthread) NULL);
		check_jvmti_error(jvmti, error, "Cannot set event notification");

	}
    /* Add jar file to boot classpath */
    add_jar_to_bootclasspath(jvmti, AGENT_JAR_FILE);
    if (!gdata->nothreads) {
		error = (*jvmti)->SetEventNotificationMode(jvmti, JVMTI_ENABLE,
				JVMTI_EVENT_THREAD_START, (jthread) NULL);
		check_jvmti_error(jvmti, error, "Cannot set event notification");

		error = (*jvmti)->SetEventNotificationMode(jvmti, JVMTI_ENABLE,
				JVMTI_EVENT_THREAD_END, (jthread) NULL);
		check_jvmti_error(jvmti, error, "Cannot set event notification");
	}
    /* Here we create a raw monitor for our use in this agent to
     *   protect critical sections of code.
     */
    error = (*jvmti)->CreateRawMonitor(jvmti, "agent data", &(gdata->lock));
    check_jvmti_error(jvmti, error, "Cannot create raw monitor");
    if (!gdata->nocpu) {
		error = (*jvmti)->CreateRawMonitor(jvmti, "agent thread",
				&(gdata->threadLock));
		check_jvmti_error(jvmti, error, "Cannot create raw monitor for agent");
	}
	error = (*jvmti)->CreateRawMonitor(jvmti, "gc thread",
			&(gdata->gcLock));
	check_jvmti_error(jvmti, error, "Cannot create raw monitor for gc");
    /* We return JNI_OK to signify success */
    return JNI_OK;
}

/* Agent_OnUnload: This is called immediately before the shared library is
 *   unloaded. This is the last code executed.
 */
JNIEXPORT void JNICALL
Agent_OnUnload(JavaVM *vm)
{
    /* Skip any cleanup, VM is about to die anyway */
}
