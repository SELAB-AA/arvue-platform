/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.loadbalancer.listener;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.PrintStream;
import java.net.MalformedURLException;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.URL;
import java.rmi.RemoteException;
import java.text.MessageFormat;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;
import org.apache.commons.io.IOUtils;
import org.junit.After;
import org.junit.AfterClass;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;
import static org.junit.Assert.*;
import org.vaadin.arvue.application.Application;
import org.vaadin.arvue.application.ApplicationStatus;
import org.vaadin.arvue.application.listener.ApplicationListener;
import org.vaadin.arvue.application.listener.ApplicationListenerImplementation;
import org.vaadin.arvue.application.repository.ApplicationRepositoryException;
import org.vaadin.arvue.application.repository.ApplicationRepositoryFactory;
import org.vaadin.arvue.application.server.ApplicationServer;
import org.vaadin.arvue.application.server.DeploymentException;
import org.vaadin.arvue.application.server.DeploymentException.Reason;
import org.vaadin.arvue.application.server.PerformanceException;
import org.vaadin.arvue.application.server.ServerStatus;
import org.vaadin.arvue.registry.ArvueRegistry;

/**
 *
 * @author bbyholm
 */
public class LoadBalancerListenerTest {
	private LoadBalancerListener instance;
	private static DummyProvisioner dummyProvisioner;
	private ApplicationListener applicationListener;

	public LoadBalancerListenerTest() {
	}

	@BeforeClass
	public static void setUpClass() throws Exception {
		dummyProvisioner = DummyProvisioner.getInstance();
		new Thread(dummyProvisioner).start();
		InputStream is = LoadBalancerListenerTest.class.getClassLoader().getResourceAsStream("haproxytest.conf");
		OutputStream os = new FileOutputStream("/tmp/haproxy.conf");
		IOUtils.copy(is, os);
		IOUtils.closeQuietly(is);
		IOUtils.closeQuietly(os);
		Runtime.getRuntime().exec("/usr/sbin/haproxy -f /tmp/haproxy.conf -p /tmp/haproxy.pid");
	}

	@AfterClass
	public static void tearDownClass() throws Exception {
		dummyProvisioner.stop();

		BufferedReader reader;
		try {
			File f = new File("/tmp/haproxy.pid");
			reader = new BufferedReader(new FileReader(f));
			try {
				boolean anythingToKill = false;
				StringBuilder sb = new StringBuilder("kill -15");
				String line;
				while ((line = reader.readLine()) != null) {
					anythingToKill = true;
					sb.append(' ').append(line);
				}

				if (anythingToKill) {
					Runtime.getRuntime().exec(sb.toString());
				}
			} finally {
				reader.close();
			}
			f.delete();
		} catch (IOException ex) {
			Logger.getLogger(LoadBalancerListenerTest.class.getName()).log(Level.SEVERE, ex.getMessage(), ex);
		}
	}

	@Before
	public void setUp() {
		try {
			ArvueRegistry appServerRegistry = new ArvueRegistry();
			applicationListener = new ApplicationListenerImplementation(null, appServerRegistry);
			Application app = new Application("Application1");
			app.setAvailable(true);
			applicationListener.addDeployedApplication(app, null);
			app = new Application("Application2");
			app.setAvailable(true);
			applicationListener.addDeployedApplication(app, null);
			instance = new LoadBalancerListener(applicationListener, appServerRegistry);
		} catch (RemoteException ex) {
			throw new RuntimeException(ex.getMessage(), ex);
		}
	}

	@After
	public void tearDown() {
	}

	/**
	 * Test of setApplications method, of class LoadBalancerListener.
	 */
	@Test
	public void testAvailableApplication() throws RemoteException {
		System.out.println("testAvailableApplication");
		try {
			URL url = new URL("http://localhost:8080/Application1");
			BufferedReader reader = new BufferedReader(new InputStreamReader(url.openStream()));
			String line;
			StringBuilder sb = new StringBuilder();

			while ((line = reader.readLine()) != null) {
				sb.append(line).append(System.getProperty("line.separator"));
			}
			reader.close();

			System.out.println(sb.toString());
		} catch (MalformedURLException ex) {
			throw new RuntimeException(ex.getMessage(), ex);
		} catch (IOException ex) {
			throw new RuntimeException(ex.getMessage(), ex);
		}

		Application app = applicationListener.getDeployedApplicationMap().get("Application1");


		try {
			synchronized (app) {
				app.wait();
			}
		} catch (InterruptedException ex) {
			Logger.getLogger(LoadBalancerListenerTest.class.getName()).log(Level.SEVERE, null, ex);
		}


		System.out.println(MessageFormat.format("Average Response Time: {0}", app.getAverageResponseTime()));
		System.out.println(MessageFormat.format("Request Count: {0}", app.getRequestCount()));

		assertTrue(app.getRequestCount() != 0);

	}

	static class DummyProvisioner implements Runnable {
		private static DummyProvisioner instance;
		private static final int port = 8081;
		private static final ServerSocket socket;
		private static volatile boolean done;

		private DummyProvisioner() {
		}

		static DummyProvisioner getInstance() {
			if (instance == null) {
				instance = new DummyProvisioner();
			}

			return instance;
		}


		static {
			try {
				socket = new ServerSocket(port);
			} catch (IOException ex) {
				throw new RuntimeException(ex.getMessage(), ex);
			}
		}

		public void run() {
			while (!done) {
				Socket listen_socket = null;
				try {
					listen_socket = socket.accept();
					PrintStream outStream = new PrintStream(listen_socket.getOutputStream());
					outStream.println("HTTP/1.0 200 OK\r\nContent-Type: text/html\r\nContent-Length: 21\r\n\r\nDeployed application!");
				} catch (IOException ex) {
					throw new RuntimeException(ex.getMessage(), ex);
				} finally {
					if (listen_socket != null) {
						try {
							listen_socket.close();
						} catch (IOException ex) {
							Logger.getLogger(LoadBalancerListenerTest.class.getName()).log(Level.SEVERE, ex.getMessage(), ex);
						}
					}
				}

			}
		}

		public void stop() {
			done = true;
		}
	}

	private static class ApplicationServerMock implements ApplicationServer {
		private static int count;
		private String name;
		private final Map<String, Application> deployedApps;

		static {

		}

		ApplicationServerMock() {
			name = "ApplicationServer" + count++;
			deployedApps = Collections.synchronizedMap(new HashMap<String, Application>());
		}

		public String getName() throws RemoteException {
			return name;
		}

		public void deploy(String appName) throws RemoteException, DeploymentException {
			Application application = new Application(appName, null);
			application.setAvailable(true);
			deployedApps.put(appName, application);
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
			throw new UnsupportedOperationException("Not supported yet.");
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
		if (applicationName == null) {
			throw new IllegalArgumentException("applicationName cannot be null");
		}

		synchronized (deployedApps) {
			Application application = deployedApps.get(applicationName);
			if (application != null) {
				if (application.isAvailable()) {
					application.addResponseTime(responseTime);
				}
			} else {
				throw new DeploymentException(Reason.NOT_DEPLOYED, "Application " + applicationName + "is not deployed.");
			}
		}
	}

		public String getInstanceID() throws RemoteException {
			throw new UnsupportedOperationException("Not supported yet.");
		}

		public ApplicationStatus[] applicationStatus() throws RemoteException {
			throw new UnsupportedOperationException("Not supported yet.");
		}

	}
}
