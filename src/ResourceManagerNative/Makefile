LIBNAME=ResourceManagerNative
SOURCES=src/ArvueJVMTIAgent.c src/callbacks.c src/gc.c src/init.c src/resource_handlers.c  src/thread_utils.c src/agent_util.c src/data_utils.c src/info_interface.c src/java_crw_demo.c src/resource_limits.c
JDK=/opt/jdk1.6.0_11
OPT=true
OSNAME=linux

COMMON_FLAGS=-fno-strict-aliasing -fPIC -fno-omit-frame-pointer
COMMON_FLAGS+= -W -Wall  -Wno-unused -Wno-parentheses
ifeq ($(OPT), true)
	CFLAGS=-O2 $(COMMON_FLAGS) 
else
	CFLAGS=-g $(COMMON_FLAGS) 
endif
OBJECTS=$(SOURCES:%.c=%.o)
LIBRARY=lib$(LIBNAME).so
LDFLAGS=-Wl,-soname=$(LIBRARY) -static-libgcc -mimpure-text
LIBRARIES=-L $(JDK)/jre/lib/$(LIBARCH) -lc
LINK_SHARED=$(LINK.c) -shared -o $@

CFLAGS += -Iinc
CFLAGS += -I$(JDK)/include -I$(JDK)/include/$(OSNAME)

all: $(LIBRARY)

$(LIBRARY): $(OBJECTS)
	$(LINK_SHARED) $(OBJECTS) $(LIBRARIES)

clean:
	rm -f $(LIBRARY) $(JARFILE) $(OBJECTS)
