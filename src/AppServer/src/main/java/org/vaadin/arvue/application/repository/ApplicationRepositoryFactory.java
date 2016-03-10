/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.application.repository;

import java.io.Serializable;

/**
 *
 * @author bbyholm
 */
public interface ApplicationRepositoryFactory extends Serializable {
	public ApplicationRepository getRepository() throws ApplicationRepositoryException;
}
