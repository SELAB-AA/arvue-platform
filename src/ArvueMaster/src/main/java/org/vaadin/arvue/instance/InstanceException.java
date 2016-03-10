/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.instance;

/**
 *
 * @author bbyholm
 */
public class InstanceException extends Exception {
	private static final long serialVersionUID = -4751005508788952198L;

	public InstanceException(String message) {
		super(message);
	}

	public InstanceException(Throwable reason) {
		super(reason);
	}

	public InstanceException(String message, Throwable reason) {
		super(message, reason);
	}
}
