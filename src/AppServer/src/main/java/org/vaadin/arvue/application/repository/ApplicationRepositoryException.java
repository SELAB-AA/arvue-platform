/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.application.repository;

/**
 *
 * @author bbyholm
 */
public class ApplicationRepositoryException extends Exception {
	private static final long serialVersionUID = 3274624286799744859L;
	ApplicationRepositoryException(Exception ex) {
		super(ex);
	}

	ApplicationRepositoryException(String msg) {
		super(msg);
	}
}
