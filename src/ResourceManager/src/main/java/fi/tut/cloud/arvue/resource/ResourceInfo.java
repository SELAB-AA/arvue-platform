package fi.tut.cloud.arvue.resource;

public class ResourceInfo {
	public String sessionId; // Thread group name (e.g. application instance)
	public long memUsage; // Heap memory used
	public long cpuUsage; // CPU time used (in nanoseconds)
	public int noThreads; // Number of threads used in instance
	public int interrupts; // How many times the instance has been interrupted (i.e. limits are exceed)
	public long memUsageLimit; // Limit for memory used (-1 no limits)
	public long cpuUsageLimit; // Limit for cpu time (nanoseconds, -1 no limits)
	public long cpuThreadUsageLimit; // Limit for cpu time usage per thread (nanoseconds, -1 no limits)
	public int noThreadsLimit; // Limit for number of threads
	public int maxInterrupts; // How many thread interrupts are sent before thread is stopped
	public String timestamp; // When the instance has been started

	// Get above information for single thread group (e.g. application instance)
	public native void update(ThreadGroup group);
	// Get array of information for all instances
	static public native ResourceInfo[] getAll();
	// Update group infos
	static public native void gc();
}