/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.instance.manager;

import com.amazonaws.auth.AWSCredentials;
import com.amazonaws.auth.BasicAWSCredentials;
import java.util.HashSet;
import java.util.Set;
import org.junit.After;
import org.junit.AfterClass;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;
import static org.junit.Assert.*;
import org.vaadin.arvue.instance.InstanceException;
import org.vaadin.arvue.instance.ServerInstance;

/**
 *
 * @author bbyholm
 */
public class EC2InstanceManagerTest {
	private static EC2InstanceManager instanceManager;

	public EC2InstanceManagerTest() {
	}

	@BeforeClass
	public static void setUpClass() throws Exception {
		String accessKey = System.getProperty("AWSAccessKey");
		if (accessKey == null || accessKey.isEmpty()) {
			throw new RuntimeException("No aws access key set!");
		}
		String privateKey = System.getProperty("AWSPrivateKey");
		if (privateKey == null || privateKey.isEmpty()) {
			throw new RuntimeException("No aws private key set!");
		}
		AWSCredentials credentials = new BasicAWSCredentials(accessKey, privateKey);
		instanceManager = new EC2InstanceManager(credentials);
	}

	@AfterClass
	public static void tearDownClass() throws Exception {
		Set<ServerInstance> instances = instanceManager.listInstances();
		if (!instances.isEmpty()) {
			instanceManager.removeInstances(instances);
		}
	}

	@Before
	public void setUp() {
	}

	@After
	public void tearDown() {
	}

	/**
	 * Test of addInstance method, of class EC2InstanceManager.
	 */
	@Test
	public void testAddInstance_Zero() throws InstanceException {
		System.out.println("add 0 Instances");

		int oldSize = instanceManager.listInstances().size();

		instanceManager.addInstance(0);
		assertEquals(instanceManager.listInstances().size(), oldSize);
	}

	/**
	 * Test of addInstance method, of class EC2InstanceManager.
	 */
	@Test
	public void testAddRemoveInstance_One() throws InstanceException {
		System.out.println("add and remove 1 Instance");

		Set<ServerInstance> oldInstances = new HashSet<ServerInstance>(instanceManager.listInstances());
		int oldSize = oldInstances.size();

		instanceManager.addInstance(1);
		assertEquals(instanceManager.listInstances().size(), oldSize + 1);

		Set<ServerInstance> newInstances = new HashSet<ServerInstance>(instanceManager.listInstances());

		newInstances.removeAll(oldInstances);

		ServerInstance[] instances = new ServerInstance[1];
		newInstances.toArray(instances);

		instanceManager.removeInstance(instances[0]);

		assertEquals(instanceManager.listInstances().size(), oldSize);
	}
}
