/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.application.server;

import java.io.BufferedReader;
import java.io.FileInputStream;
import java.io.FileReader;
import java.io.IOException;
import java.util.NoSuchElementException;
import java.util.Scanner;
import java.util.regex.Pattern;

/**
 *
 * @author bbyholm
 */
class Performance {
	static float getCpuLoad() throws PerformanceException {
		if (isWindows()) {
			return -1;
		}
		String fName = "/proc/loadavg";
			try {
				/* $ cat /proc/loadavg
				 * 0.17 0.14 0.10 1/379 6901
				 */
				BufferedReader r = new BufferedReader(new FileReader(fName));
				try {
					String[] loadAverages = r.readLine().split(" ", 4);
					return Float.parseFloat(loadAverages[0]) / getCpuCount();
				} finally {
					r.close();
				}

			} catch (IOException ex) {
				throw new PerformanceException("Could not get cpu load.", ex);
			}
	}

	static float getMemLoad() throws PerformanceException {
		if (isWindows()) {
			java.lang.management.OperatingSystemMXBean mxbean = java.lang.management.ManagementFactory.getOperatingSystemMXBean();
			com.sun.management.OperatingSystemMXBean sunmxbean = (com.sun.management.OperatingSystemMXBean) mxbean;
			long freeMemory = sunmxbean.getFreePhysicalMemorySize();
			long availableMemory = sunmxbean.getTotalPhysicalMemorySize();
			return 1 - ((float) freeMemory) / availableMemory;
		}
		String fName = "/proc/meminfo";
		try {
			FileInputStream f = new FileInputStream(fName);

			/* $ cat /proc/meminfo
			 * MemTotal:        2056964 kB
			 * MemFree:           16716 kB
			 * Buffers:            9776 kB
			 * Cached:           127220 kB
			 */
			Scanner scanner = new Scanner(f).useDelimiter("\\D+");
			try {
				long memTotal = scanner.nextLong();
				long memFree = scanner.nextLong();
				long buffers = scanner.nextLong();
				long cached = scanner.nextLong();

				return 1 - ((float) (memFree + buffers + cached)) / memTotal;
			} catch (NoSuchElementException ex) {
				throw new PerformanceException("Could not get memory load.", ex);
			} catch (ArithmeticException ex) {
				throw new PerformanceException("Could not get memory load.", ex);
			} finally {
				scanner.close();
			}
		} catch (IOException ex) {
			throw new PerformanceException("Could not get memory load.", ex);
		}
	}

        private static boolean isWindows() {
            String os = System.getProperty("os.name").toLowerCase();
	    return os.indexOf("win") >= 0;

	}

	/**
	 * @return
	 */
	private static int getCpuCount() throws PerformanceException {
		String fName = "/proc/cpuinfo";
		int processors = 0;

		try {
			BufferedReader reader = new BufferedReader(new FileReader(fName));
				String line;
				Pattern p = Pattern.compile("^processor");
				try {
					while ((line = reader.readLine()) != null) {
						if (p.matcher(line).find()) {
							processors++;
						}
					}
				} finally {
					reader.close();
				}
		} catch (IOException ex) {
			throw new PerformanceException("Could not get cpu count.", ex);
		}

		if (processors == 0) {	// method invariant postcondition -- processors may not be zero
			throw new PerformanceException("Could not get cpu count.", new Exception());
		}

		return processors;
	}
}
