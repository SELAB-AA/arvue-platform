#ifndef MACROS_H
#define MACROS_H

#define RESOURCE_MANAGER_class           fi/tut/cloud/arvue/resource/ResourceTracker /* Name of class we are using */
#define RESOURCE_MANAGER_newobj        newobj   /* Name of java init method */
#define RESOURCE_MANAGER_newarr        newarr   /* Name of java newarray method */
#define RESOURCE_MANAGER_native_newobj _newobj  /* Name of java newobj native */
#define RESOURCE_MANAGER_native_newarr _newarr  /* Name of java newarray native */
#define RESOURCE_MANAGER_engaged       engaged  /* Name of static field switch */

/* C macros to create strings from tokens */
#define _STRING(s) #s
#define STRING(s) _STRING(s)

#define debug_message stdout_message
#endif
