/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.loadbalancer.listener;

import java.net.SocketAddress;
import java.rmi.AccessException;
import java.rmi.NotBoundException;
import java.rmi.Remote;
import java.rmi.RemoteException;
import java.text.ParseException;
import java.util.Date;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.productivity.java.syslog4j.server.SyslogServer;
import org.productivity.java.syslog4j.server.SyslogServerConfigIF;
import org.productivity.java.syslog4j.server.SyslogServerEventIF;
import org.productivity.java.syslog4j.server.SyslogServerIF;
import org.productivity.java.syslog4j.server.SyslogServerSessionEventHandlerIF;
import org.vaadin.arvue.application.Application;
import org.vaadin.arvue.application.listener.ApplicationListener;
import org.vaadin.arvue.application.server.ApplicationServer;
import org.vaadin.arvue.application.server.DeploymentException;
import org.vaadin.arvue.registry.ArvueRegistry;

/**
 *
 * @author bbyholm
 */
public class LoadBalancerListener {
	private static final String protocol = "udp";
	private static final String host = "localhost";
	private static final int port = 1212;

	private SyslogServerIF syslogServer;
	private SyslogServerConfigIF syslogServerConfig;
	private SyslogMessageHandler eventHandler;
	private ApplicationListener applicationListener;
	private ArvueRegistry appServerRegistry;

	public LoadBalancerListener(ApplicationListener applicationListener, ArvueRegistry appServerRegistry) {
		this.applicationListener = applicationListener;
		this.appServerRegistry = appServerRegistry;

		syslogServer = SyslogServer.getInstance(protocol);
		syslogServerConfig = syslogServer.getConfig();
		syslogServerConfig.setHost(host);
        syslogServerConfig.setPort(port);

		eventHandler = new SyslogMessageHandler();
		syslogServerConfig.addEventHandler(eventHandler);
		SyslogServer.getThreadedInstance(protocol);
	}

	/**
	 * @param applications the applications to set
	 */
	//public void setApplications(Map<String, Application> applications) {
	//	this.applications = applications;
	//}

	/**
	 * @return the protocol
	 */
	public static String getProtocol() {
		return protocol;
	}

	/**
	 * @return the host
	 */
	public static String getHost() {
		return host;
	}

	/**
	 * @return the port
	 */
	public static int getPort() {
		return port;
	}

	private class SyslogMessageHandler implements SyslogServerSessionEventHandlerIF {
		private static final long serialVersionUID = -5623762368442865111L;
		private final Pattern applicationNamePattern = Pattern.compile("^GET\\s+/([^\\s\\?]*)(\\?\\S*)?\\s+HTTP/1\\.\\d$");

		public void event(Object session, SyslogServerIF syslogServer, SocketAddress socketAddress, SyslogServerEventIF event) {
			//Logger.getLogger(LoadBalancerListener.class.getName()).log(Level.INFO, "event()");

			try {
				HTTPLogInfo info = new HTTPLogInfo(event.getMessage());
				Matcher matcher = applicationNamePattern.matcher(info.getHttp_request());
				if (matcher.matches()) {
					Application app = applicationListener.getDeployedApplicationMap().get(matcher.group(1));

					if (app != null) {
						synchronized (app) {
							if (app.isAvailable()) {
								//Logger.getLogger(LoadBalancerListener.class.getName()).log(Level.INFO, "adding response time {0}", info.getTr());

								Remote remote = appServerRegistry.lookup(info.getServer_name());
								if (remote instanceof ApplicationServer) {
									ApplicationServer applicationServer = (ApplicationServer) remote;
									try {
										applicationServer.addResponseTime(matcher.group(1), info.getTr());
										//app.notify();
									} catch (DeploymentException ex) {
										Logger.getLogger(LoadBalancerListener.class.getName()).log(Level.SEVERE, null, ex);
									}
								}
							}
						}
					}
				}
			} catch (NotBoundException ex) {
				//Logger.getLogger(LoadBalancerListener.class.getName()).log(Level.WARNING, null, ex);
			} catch (AccessException ex) {
				Logger.getLogger(LoadBalancerListener.class.getName()).log(Level.SEVERE, null, ex);
			} catch (RemoteException ex) {
				Logger.getLogger(LoadBalancerListener.class.getName()).log(Level.SEVERE, null, ex);
			} catch (ParseException ex) {
				//Logger.getLogger(LoadBalancerListener.class.getName()).log(Level.WARNING, null, ex);
			}

		}

		public void exception(Object session, SyslogServerIF syslogServer, SocketAddress socketAddress, Exception exception) {
			Logger.getLogger(LoadBalancerListener.class.getName()).log(Level.INFO, "exception()");
		}

		public Object sessionOpened(SyslogServerIF syslogServer, SocketAddress socketAddress) {
			Logger.getLogger(LoadBalancerListener.class.getName()).log(Level.INFO, "sessionOpened()");
			return new Date();
		}

		public void sessionClosed(Object session, SyslogServerIF syslogServer, SocketAddress socketAddress, boolean timeout) {
			Logger.getLogger(LoadBalancerListener.class.getName()).log(Level.INFO, "sessionClosed() {0}", session);
		}

		public void initialize(SyslogServerIF syslogServer) {
			Logger.getLogger(LoadBalancerListener.class.getName()).log(Level.INFO, "initialize()");
		}

		public void destroy(SyslogServerIF syslogServer) {
			Logger.getLogger(LoadBalancerListener.class.getName()).log(Level.INFO, "destroy()");
		}


	}
}
