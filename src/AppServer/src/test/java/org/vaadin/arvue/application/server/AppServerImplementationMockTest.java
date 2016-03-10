/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.application.server;

import java.rmi.RemoteException;
import java.util.HashMap;
import org.junit.Before;
import org.junit.Test;
import org.mockito.Mock;
import static org.mockito.Mockito.*;
import org.vaadin.arvue.application.Application;
import org.vaadin.arvue.application.repository.ApplicationRepository;
import org.vaadin.arvue.application.repository.ApplicationRepositoryException;
import org.vaadin.arvue.application.repository.ApplicationRepositoryFactory;

/**
 *
 * @author bbyholm
 */
public class AppServerImplementationMockTest extends MockTest {
	private ApplicationServerImplementation instance = ApplicationServerImplementation.getInstance();
	private @Mock ApplicationRepositoryFactory repoFactory;
	private @Mock ApplicationRepository	mockRepo;
	private Application testApp;


	@Before public void setup() throws RemoteException, ApplicationRepositoryException {
		testApp = new Application("TestApp", null);

		when(repoFactory.getRepository()).thenReturn(mockRepo);
		when(mockRepo.hasApp(testApp)).thenReturn(true);

		//ApplicationServerImplementation.setDeployedApps(new HashMap<String, Application>());
		instance.setRepositoryFactory(repoFactory);
	}

	@Test
	public void testDeploy_mockrepo_goodName() throws RemoteException, DeploymentException, ApplicationRepositoryException {
		System.out.println("deploy1");

		instance.deploy(testApp.getName(), testApp.getVersion());
	}

	@Test
	public void testDeploy_mockrepo_goodName2() throws RemoteException, DeploymentException, ApplicationRepositoryException {

		System.out.println("deploy2");

		instance.deploy(testApp.getName(), testApp.getVersion());
	}

	@Test(expected = DeploymentException.class)
	public void testDeploy_mockrepo_goodName3() throws RemoteException, DeploymentException, ApplicationRepositoryException {

		System.out.println("deploy3");

		instance.deploy(testApp.getName(), testApp.getVersion());
		instance.deploy(testApp.getName(), testApp.getVersion());
	}
}
