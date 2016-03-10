/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.application.server;

import java.io.Serializable;
import java.util.Map;

/**
 *
 * @author User
 */
public class ServerStatus implements Serializable, Comparable<ServerStatus> {
	private static final long serialVersionUID = -2611276002870894183L;
	private final String name;
	private final float cpuLoad;
	private final float memLoad;
	private final Map<String, Float> responseTimes;

	ServerStatus(String name, float cpuLoad, float memLoad, Map<String, Float> responseTimes) {
		this.name = name;
		this.cpuLoad = cpuLoad;
		this.memLoad = memLoad;
		this.responseTimes = responseTimes;
	}

	@Override
	public String toString() {
		StringBuilder sb = new StringBuilder(14)
				.append(getCpuLoad())
				.append(" ")
				.append(getMemLoad())
				.append(" ")
				.append(getResponseTimes());
		return sb.toString();
	}

	/**
	 * @return the cpuLoad
	 */
	public float getCpuLoad() {
		return cpuLoad;
	}

	/**
	 * @return the memLoad
	 */
	public float getMemLoad() {
		return memLoad;
	}

	/**
	 * @return the responseTime
	 */
	public Map<String, Float> getResponseTimes() {
		return responseTimes;
	}

	/**
	 * @return the name
	 */
	public String getName() {
		return name;
	}

	public int compareTo(ServerStatus t) {
		if (this == t) {
			return 0;
		}

		if (t == null) {
			return 1;
		}

		float this_avg = (getMemLoad() + getCpuLoad()) / 2;
		float that_avg = (t.getMemLoad() + t.getCpuLoad()) / 2;

		return Math.round(this_avg - that_avg);

	}
}