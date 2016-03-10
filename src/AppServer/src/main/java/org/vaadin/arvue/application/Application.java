
/*
* To change this template, choose Tools | Templates
* and open the template in the editor.
 */
package org.vaadin.arvue.application;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.Collection;

/**
 *
 * @author User
 */
public class Application implements Serializable, Comparable<Application> {
    private static final long	serialVersionUID = 3L;
    private final String		name;
    private final Version		version;
	private final Collection<Integer>responseTimes = new ArrayList<Integer>();
	private long				requestCount;
	private boolean             available;

    public Application(String name) {
        this(name, null);
    }

    public Application(String name, String version) {
        if (name == null) {
            throw new IllegalArgumentException("name cannot be null");
        } else if (name.isEmpty()) {
            throw new IllegalArgumentException("name cannot be empty");
        }

        this.name = name;

        if ((version == null) || version.isEmpty()) {
            this.version = null;
        } else {
            this.version = new Version(version);
        }
    }

    /**
     * @return the version or null if no version set
     */
    public String getVersion() {
        return (version == null)
               ? null
               : version.toString();
    }

    /**
     * @return the name
     */
    public String getName() {
        return name;
    }

	/**
	 * Adds a response time
	 * @param responseTime the response time (in milliseconds) to add
	 */
	public void addResponseTime(int responseTime) {
		if (requestCount++ > 0) {
			synchronized (responseTimes) {
				responseTimes.add(responseTime);
			}
		}
	}

	/**
	 * @return the averageResponseTime
	 */
	public float getAverageResponseTime() {
		synchronized (responseTimes) {
			if (responseTimes.isEmpty()) {
				return 0.0f;
			} else {
				int sum = 0;
				for (int time : responseTimes) {
					sum += time;
				}
				float result = (float) sum / responseTimes.size();
				responseTimes.clear();
				return result;
			}
		}
	}

    @Override
    public boolean equals(Object obj) {
        if (this == obj) {
            return true;
        }

        if (obj instanceof Application) {
            Application that = (Application) obj;

            if (this.getName().equals(that.getName())) {
                if ((this.getVersion() == null) && (that.getVersion() == null)) {
                    return true;
                } else if ((this.getVersion() == null) || (that.getVersion() == null)) {
                    return false;
                } else {
                    return this.getVersion().equals(that.getVersion());
                }
            } else {
                return false;
            }
        } else {
            return false;
        }
    }

    @Override
    public int hashCode() {
        int hash = 7;

        hash = 17 * hash + ((this.version != null)
                            ? this.version.hashCode()
                            : 0);
        hash = 17 * hash + ((this.name != null)
                            ? this.name.hashCode()
                            : 0);

        return hash;
    }

	/**
	 * @return the bundleName
	 */
	public String getBundleName() {
		StringBuilder sb = new StringBuilder(14 + 64).append("com.arvue.").append(getName()).append(".jar");
		return sb.toString();
	}

	/**
	 * @return the requestCount
	 */
	public long getRequestCount() {
		return requestCount;
	}

	public int compareTo(Application t) {
		if (this == t) {
			return 0;
		}

		if (t == null) {
			return 1;
		}

		int result = getName().compareTo(t.getName());

		if (result == 0) {
			String thisVersion = getVersion();
			String thatVersion = t.getVersion();
			if (thisVersion != null) {
				return thisVersion.compareTo(thatVersion);
			} else if (thatVersion != null) {
				return -1;
			} else {
				return 0;
			}
		}

		return result;
	}

	/**
	 * @return the available
	 */
	public boolean isAvailable() {
		return available;
	}

	/**
	 * @param available the available to set
	 */
	public void setAvailable(boolean available) {
		this.available = available;
	}
}