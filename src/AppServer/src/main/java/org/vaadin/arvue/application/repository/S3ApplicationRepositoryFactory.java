/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.application.repository;

/**
 *
 * @author bbyholm
 */
public class S3ApplicationRepositoryFactory implements ApplicationRepositoryFactory {
	private static final long serialVersionUID = 9047533739107204270L;
	private final String name;
	private final String accessKey;
	private final String privateKey;

	public S3ApplicationRepositoryFactory(String name, String accessKey, String privateKey) {
		if (name == null) {
			throw new IllegalArgumentException("name cannot be null");
		}
		if (accessKey == null) {
			throw new IllegalArgumentException("accessKey cannot be null");
		}
		if (privateKey == null) {
			throw new IllegalArgumentException("privatekey cannot be null");
		}
		this.name = name;
		this.accessKey = accessKey;
		this.privateKey = privateKey;
	}

	@Override
	public ApplicationRepository getRepository() throws ApplicationRepositoryException {
		return new S3ApplicationRepository(name, accessKey, privateKey);
	}

}
