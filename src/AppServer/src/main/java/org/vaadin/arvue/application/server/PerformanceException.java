/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.application.server;

/**
 *
 * @author bbyholm
 */
public class PerformanceException extends Exception {
	private static final long serialVersionUID = -6248893455344403967L;
    Exception hiddenException;

    PerformanceException(String msg, Exception ex) {
        super(msg);
        hiddenException = ex;
    }

    Exception getHiddenException() {
        return hiddenException;
    }
}
