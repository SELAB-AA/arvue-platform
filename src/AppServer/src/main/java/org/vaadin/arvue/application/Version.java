
/*
* To change this template, choose Tools | Templates
* and open the template in the editor.
 */
package org.vaadin.arvue.application;

//~--- JDK imports ------------------------------------------------------------

import java.io.Serializable;

/**
 *
 * @author User
 */
class Version implements Comparable<Version>, Serializable {
    private static final String delimiter     = "\\.";
    private static final String formatMessage =
        "Bad version string. Correct format is: major[.minor[.build[.revision]]]";
    private static final String negativeMessage  = "Version numbers cannot be negative!";
    private static final long   serialVersionUID = 2L;
    private int                 build            = -1;
    private int                 major            = -1;
    private int                 minor            = -1;
    private int                 revision         = -1;

    Version(int major) {
        if (major < 0) {
            throw new IllegalArgumentException(negativeMessage);
        }

        this.major = major;
    }

    Version(String version) {
        if (version == null) {
            throw new IllegalArgumentException("Version cannot be null!");
        }

        String[] tokens = version.split(delimiter);

        if (tokens.length > 4) {
            throw new IllegalArgumentException(formatMessage);
        }

        try {
            this.major = Integer.valueOf(tokens[0]);

            if (this.major < 0) {
                throw new IllegalArgumentException(negativeMessage);
            }

            if (tokens.length > 1) {
                this.minor = Integer.valueOf(tokens[1]);

                if (this.minor < 0) {
                    throw new IllegalArgumentException(negativeMessage);
                }
            }

            if (tokens.length > 2) {
                this.build = Integer.valueOf(tokens[2]);

                if (this.build < 0) {
                    throw new IllegalArgumentException(negativeMessage);
                }
            }

            if (tokens.length > 3) {
                this.revision = Integer.valueOf(tokens[3]);

                if (this.revision < 0) {
                    throw new IllegalArgumentException(negativeMessage);
                }
            }
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException(formatMessage);
        }
    }

    Version(int major, int minor) {
        if ((major < 0) || (minor < 0)) {
            throw new IllegalArgumentException(negativeMessage);
        }

        this.major = major;
        this.minor = minor;
    }

    Version(int major, int minor, int build) {
        this(major, minor, build, 0);
    }

    Version(int major, int minor, int build, int revision) {
        if ((major < 0) || (minor < 0) || (build < 0) || (revision < 0)) {
            throw new IllegalArgumentException(negativeMessage);
        }

        this.major    = major;
        this.minor    = minor;
        this.build    = build;
        this.revision = revision;
    }

    /**
     * @return the major version
     */
    int getMajor() {
        return major;
    }

    /**
     * @param major the major version to set
     */
    void setMajor(int major) {
        if (major < 0) {
            throw new IllegalArgumentException(negativeMessage);
        }

        this.major = major;
    }

    /**
     * @return the minor version
     */
    int getMinor() {
        return (minor < 0)
               ? 0
               : minor;
    }

    /**
     * @param minor the minor version to set
     */
    void setMinor(int minor) {
        if (minor < 0) {
            throw new IllegalArgumentException(negativeMessage);
        }

        this.minor = minor;
    }

    /**
     * @return the build number
     */
    int getBuild() {
        return (build < 0)
               ? 0
               : build;
    }

    /**
     * @param build the build number to set
     */
    void setBuild(int build) {
        if (build < 0) {
            throw new IllegalArgumentException(negativeMessage);
        }

        this.build = build;
    }

    /**
     * @return the revision
     */
    int getRevision() {
        return (revision < 0)
               ? 0
               : revision;
    }

    /**
     * @param revision the revision to set
     */
    void setRevision(int revision) {
        if (revision < 0) {
            throw new IllegalArgumentException(negativeMessage);
        }

        this.revision = revision;
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder(43);

        sb.append(major);

        if ((minor >= 0) || (build >= 0) || (revision >= 0)) {
            sb.append(".").append(getMinor());
        }

        if ((build >= 0) || (revision >= 0)) {
            sb.append(".").append(getBuild());
        }

        if (revision >= 0) {
            sb.append(".").append(revision);
        }

        return sb.toString();
    }

    @Override
    public int compareTo(Version v) {
		if (this == v) {
			return 0;
		}

		if (v == null) {
			return 1;
		}

		
        if (getMajor() < v.getMajor()) {
            return -1;
        } else if (getMajor() > v.getMajor()) {
            return 1;
        } else {
            if (getMinor() < v.getMinor()) {
                return -1;
            } else if (getMinor() > v.getMinor()) {
                return 1;
            } else {
                if (getBuild() < v.getBuild()) {
                    return -1;
                } else if (getBuild() > v.getBuild()) {
                    return 1;
                } else {
                    if (getRevision() < v.getRevision()) {
                        return -1;
                    } else if (getRevision() > v.getRevision()) {
                        return 1;
                    } else {
                        return 0;
                    }
                }
            }
        }
    }
}


//~ Formatted by Jindent --- http://www.jindent.com
