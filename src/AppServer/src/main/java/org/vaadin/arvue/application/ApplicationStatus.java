/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.application;

import java.io.Serializable;

/**
 *
 * @author bbyholm
 */
public class ApplicationStatus implements Serializable {
	private static final long serialVersionUID = 910301471959636966L;
	private String name;
	private float util;

	public ApplicationStatus(String name, float util) {
		this.name = name;
		this.util = util;
	}

	/**
	 * @return the name
	 */
	public String getName() {
		return name;
	}

	/**
	 * @return the util
	 */
	public float getUtil() {
		return util;
	}

}
