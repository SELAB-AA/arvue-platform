/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.application.repository;

import org.junit.Test;
import static org.junit.Assert.*;
import org.junit.BeforeClass;
import org.vaadin.arvue.application.Application;

/**
 *
 * @author bbyholm
 */
public class S3AppRepositoryTest {
	static S3ApplicationRepository instance;
	static Application goodApp;
	static Application badApp;

	@BeforeClass
	public static void setUp() throws Exception {
		instance = new S3ApplicationRepository("arvue-repo", System.getProperty("accessKey"), System.getProperty("privateKey"));
		goodApp = new Application("calc");
		badApp = new Application("dummy");
	}
	/**
	 * Test of hasApp method, of class S3ApplicationRepository.
	 */
	@Test
	public void testHasApp() {
		System.out.println("hasApp");

		assertTrue(instance.hasApp(goodApp));
		assertFalse(instance.hasApp(badApp));
	}

	/**
	 * Test of getApp method, of class S3ApplicationRepository.
	 */
	@Test
	public void testGet() throws Exception {
		System.out.println("get");
		String path = System.getProperty("java.io.tmpdir");
		instance.get(goodApp, path);
	}
}
