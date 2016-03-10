/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.loadbalancer;

import java.io.IOException;
import java.rmi.RemoteException;
import java.util.ArrayList;
import java.util.Random;
import org.vaadin.arvue.application.ApplicationStatus;
import org.vaadin.arvue.application.repository.ApplicationRepositoryException;
import org.vaadin.arvue.application.repository.ApplicationRepositoryFactory;
import org.vaadin.arvue.application.server.ApplicationServer;
import java.util.Collection;
import org.junit.After;
import org.junit.AfterClass;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;
import static org.mockito.Mockito.*;
import static org.junit.Assert.*;
import org.vaadin.arvue.application.server.DeploymentException;
import org.vaadin.arvue.application.server.PerformanceException;
import org.vaadin.arvue.application.server.ServerStatus;

/**
 *
 * @author bbyholm
 */
public class HAProxyConfigurationMockTest extends MockTest {
	private static Random rand = new Random();
	private  Collection<ApplicationServer> applicationServers;

	@BeforeClass
	public static void setUpClass() throws Exception {
	}

	@AfterClass
	public static void tearDownClass() throws Exception {
	}

	@Before
	public void setUp() {
		int size = rand.nextInt(8);
		applicationServers = new ArrayList<ApplicationServer>(size);
		for (int i = 0; i < size; i++) {
			ApplicationServer applicationServer = spy(new ApplicationServerMock());
			applicationServers.add(applicationServer);
		}
	}

	@After
	public void tearDown() {
	}

	/**
	 * Test of configure method, of class HAProxy.
	 */
	@Test
	public void testConfigure() throws IOException {
		System.out.println("configure");
		HAProxy instance = new HAProxy();
		instance.configure(applicationServers);
		Process p = Runtime.getRuntime().exec("/usr/sbin/haproxy -c -f /tmp/haproxy.conf");
		int countdown = 10;
		while (countdown-- > 0) {
			try {
				assertEquals(p.exitValue(), 0);
				return;
			} catch (IllegalThreadStateException ex) {
				try {
					Thread.sleep(10);
				} catch (InterruptedException e) {
					Thread.currentThread().interrupt();
				}
			}
		}

		//timeout

		fail("Timeout");
	}

	private static class ApplicationNameSetGenerator {
		static String[] generate() {
			int size = rand.nextInt(256);

			String[] applicationNames = new String[size];

			for (int i = 0; i < size; i++) {
				applicationNames[i] = "Application" + rand.nextInt(size);
			}

			return applicationNames;
		}
	}

	private static class ApplicationServerMock implements ApplicationServer {
		private static int count;
		private String name;

		ApplicationServerMock() {
			name = "ApplicationServer" + count++;
		}

		public String getName() throws RemoteException {
			return name;
		}

		public void deploy(String appName) throws RemoteException, DeploymentException {
			throw new UnsupportedOperationException("Not supported yet.");
		}

		public void deploy(String appName, String version) throws RemoteException, DeploymentException {
			throw new UnsupportedOperationException("Not supported yet.");
		}

		public void undeploy(String appName) throws RemoteException, DeploymentException {
			throw new UnsupportedOperationException("Not supported yet.");
		}

		public void undeploy(String appName, String version) throws RemoteException, DeploymentException {
			throw new UnsupportedOperationException("Not supported yet.");
		}

		public ServerStatus status() throws RemoteException, PerformanceException {
			throw new UnsupportedOperationException("Not supported yet.");
		}

		public void setRepositoryFactory(ApplicationRepositoryFactory repository) throws RemoteException, ApplicationRepositoryException {
			throw new UnsupportedOperationException("Not supported yet.");
		}

		public String[] getDeployedApps() throws RemoteException {
			return ApplicationNameSetGenerator.generate();
		}

		public String getDeployPath() throws RemoteException {
			throw new UnsupportedOperationException("Not supported yet.");
		}

		public void setDeployPath(String aDeployPath) throws RemoteException {
			throw new UnsupportedOperationException("Not supported yet.");
		}

		public int compareTo(ApplicationServer t) {
			throw new UnsupportedOperationException("Not supported yet.");
		}

		public int getPort() throws RemoteException {
			throw new UnsupportedOperationException("Not supported yet.");
		}

		public String getPublicAddress() throws RemoteException {
			throw new UnsupportedOperationException("Not supported yet.");
		}

		public String getPrivateAddress() throws RemoteException {
			throw new UnsupportedOperationException("Not supported yet.");
		}

		public void addResponseTime(String applicationName, int responseTime) throws RemoteException, DeploymentException {
			throw new UnsupportedOperationException("Not supported yet.");
		}

		public String getInstanceID() throws RemoteException {
			throw new UnsupportedOperationException("Not supported yet.");
		}

		public ApplicationStatus[] applicationStatus() throws RemoteException {
			throw new UnsupportedOperationException("Not supported yet.");
		}

	}
}
