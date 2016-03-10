/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.application.server;

import org.vaadin.arvue.application.repository.ApplicationRepositoryFactory;
import org.mockito.Mock;
import java.rmi.RemoteException;
import org.junit.Test;
import static org.junit.Assert.*;
import org.vaadin.arvue.application.repository.ApplicationRepositoryException;
import org.vaadin.arvue.application.repository.S3ApplicationRepositoryFactory;

/**
 *
 * @author bbyholm
 */
public class AppServerImplementationNorepoTest {
	ApplicationServer instance = ApplicationServerImplementation.getInstance();
	@Mock ApplicationRepositoryFactory repoFactory;

	/**
	 * Test of getInstance method, of class ApplicationServerImplementation.
	 */
	@Test
	public void testGetInstance() {
		System.out.println("getInstance");
		ApplicationServer a = ApplicationServerImplementation.getInstance();
		ApplicationServer b = ApplicationServerImplementation.getInstance();
		assertTrue(a == b);
	}

	/**
	 * Test of deploy method, of class ApplicationServerImplementation.
	 */
	@Test(expected = IllegalArgumentException.class)
	public void testDeploy_norepo_emptyName() throws RemoteException, DeploymentException {
		System.out.println("deploy");
		String appName = "";
		String version = "";
		instance.deploy(appName, version);
	}

	/**
	 * Test of deploy method, of class ApplicationServerImplementation.
	 */
	@Test(expected = DeploymentException.class)
	public void testDeploy_norepo_goodName() throws RemoteException, DeploymentException {
		System.out.println("deploy");
		String appName = "TestApp";
		String version = "";
		instance.deploy(appName, version);
	}

	/**
	 * Test of status method, of class ApplicationServerImplementation.
	 */
	@Test
	public void testStatus() throws RemoteException {
		System.out.println("status");

		try {
			System.out.println(instance.status());
		} catch (PerformanceException ex) {
			fail(ex.getMessage());
		}
	}

	@Test
	public void testDeployUndeploy() throws RemoteException, DeploymentException, ApplicationRepositoryException {
		System.out.println("Deploy / Undeploy");
		instance.setRepositoryFactory(new S3ApplicationRepositoryFactory("arvue-repo", System.getProperty("accessKey"), System.getProperty("privateKey")));
		assertTrue(instance.getDeployedApps().length == 0);
		instance.deploy("calc");
		assertTrue(instance.getDeployedApps().length == 1);
		instance.undeploy("calc");
		assertTrue(instance.getDeployedApps().length == 0);
	}
}
