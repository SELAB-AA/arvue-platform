#ifndef INIT_H
#define INIT_H



JNIEXPORT jint JNICALL Agent_OnLoad(JavaVM *vm, char *options, void *reserved);
JNIEXPORT void JNICALL Agent_OnUnload(JavaVM *vm);

void JNICALL cbVMStart(jvmtiEnv *jvmti, JNIEnv *env);
void JNICALL cbVMInit(jvmtiEnv *jvmti, JNIEnv *env, jthread thread);
void JNICALL cbVMDeath(jvmtiEnv *jvmti, JNIEnv *env);
#endif
