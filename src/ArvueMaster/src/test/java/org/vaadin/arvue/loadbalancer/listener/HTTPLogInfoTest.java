/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.loadbalancer.listener;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import org.junit.Test;
import static org.junit.Assert.*;

/**
 *
 * @author bbyholm
 */
public class HTTPLogInfoTest {

	@Test
	public void testHTTPLogInfo() throws ParseException {
		HTTPLogInfo info = new HTTPLogInfo("haproxy[674]: 127.0.0.1:33318 [15/Oct/2003:08:31:57.130] px-http px-http/srv1 6559/0/7/147/6723 200 243 - - ---- 5/3/3/1/0 0/0 \"HEAD / HTTP/1.0\"");
		assertEquals(info.getProcess_name(), "haproxy");
		assertEquals(info.getPid(), 674);
		assertEquals(info.getClient_ip(), "127.0.0.1");
		assertEquals(info.getClient_port(), 33318);
		assertEquals(info.getAccept_date(), new SimpleDateFormat("dd/MMM/yyyy:HH:mm:ss.SSS").parse("15/Oct/2003:08:31:57.130"));
		assertEquals(info.getFrontend_name(), "px-http");
		assertEquals(info.getBackend_name(), "px-http");
		assertEquals(info.getServer_name(), "srv1");
		assertEquals(info.getTq(), 6559);
		assertEquals(info.getTw(), 0);
		assertEquals(info.getTc(), 7);
		assertEquals(info.getTr(), 147);
		assertEquals(info.getTt(), 6723);
		assertEquals(info.getStatus_code(), 200);
		assertEquals(info.getBytes_read(), 243);
		assertEquals(info.getCaptured_request_cookie(), "-");
		assertEquals(info.getCaptured_response_cookie(), "-");
		assertEquals(info.getTermination_state(), "----");
		assertEquals(info.getActconn(), 5);
		assertEquals(info.getFeconn(), 3);
		assertEquals(info.getBeconn(), 3);
		assertEquals(info.getSrv_conn(), 1);
		assertEquals(info.getRetries(), 0);
		assertEquals(info.getSrv_queue(), 0);
		assertEquals(info.getBackend_queue(), 0);
		assertNull(info.getCaptured_request_headers());
		assertNull(info.getCaptured_response_headers());
		assertEquals(info.getHttp_request(), "HEAD / HTTP/1.0");
	}

	/* Tq, Tw Tc and Tr can be negative */
	@Test
	@SuppressWarnings("ResultOfObjectAllocationIgnored")
	public void testHTTPLogInfo2() throws ParseException {
		new HTTPLogInfo("haproxy[12653]: 127.0.0.1:59828 [10/Nov/2011:16:12:26.122] http_proxy provisioner/provisioner 54/0/0/-1/200 502 426 - - SH-- 0/0/0/0/0 0/0 \"GET /favicon.ico HTTP/1.1\"");
	}
}
