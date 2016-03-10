/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.application.server;

/**
 *
 * @author bbyholm
 */
public class DeploymentException extends Exception {
	private static final long serialVersionUID = -4515189552659488583L;

	/**
	 * @return the reason
	 */
	public Reason getReason() {
		return reason;
	}

	public static enum Reason {
		NONEXISTANT,
		NOT_DEPLOYED,
		ALREADY_DEPLOYED,
		NOREPO,
		CONNECTION,
		IO
	};

	private final Reason reason;
	private final String what;

	public DeploymentException(Reason reason) {
		this(reason, null);
	}

	public DeploymentException(Reason reason, String what) {
		super();
		this.reason = reason;
		this.what = what == null ? "" : what;
	}

	@Override
	public String toString() {
		StringBuilder sb = new StringBuilder(what);

		switch (getReason()) {
			case NONEXISTANT:
				sb.append(" does not exist.");
				break;
			case NOT_DEPLOYED:
				sb.append(" is not deployed.");
				break;
			case ALREADY_DEPLOYED:
				sb.append(" is already deployed.");
				break;
			case NOREPO:
				sb.append("No repository set.");
				break;
			case CONNECTION:
				sb.append("Error connecting to repository.");
				break;
			case IO:
				sb.append("IO Error.");
		}

		return sb.toString();
	}
}
