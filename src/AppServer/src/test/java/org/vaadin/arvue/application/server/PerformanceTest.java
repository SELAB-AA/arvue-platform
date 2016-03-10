/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.application.server;

import java.util.logging.Level;
import java.util.logging.Logger;
import org.junit.After;
import org.junit.AfterClass;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;
import static org.junit.Assert.*;

/**
 *
 * @author bbyholm
 */
public class PerformanceTest {
	/**
	 * Test of getCpuLoad method, of class Performance.
	 */
	@Test
	public void testGetCpuLoad() {
		System.out.println("getCpuLoad");
		try {
			Performance.getCpuLoad();
		} catch (PerformanceException ex) {
			fail(ex.getMessage());
		}
	}

	/**
	 * Test of getMemLoad method, of class Performance.
	 */
	@Test
	public void testGetMemLoad() throws Exception {
		System.out.println("getMemLoad");
		try {
			Performance.getMemLoad();
		} catch (PerformanceException ex) {
			fail(ex.getMessage());
		}
	}
}
