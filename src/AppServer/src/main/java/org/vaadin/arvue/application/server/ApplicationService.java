/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.application.server;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import java.io.IOException;
import java.rmi.RemoteException;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.vaadin.arvue.application.Application;
import org.vaadin.arvue.application.listener.ApplicationListener;


/**
 *
 * @author bbyholm
 */
public class ApplicationService implements HttpHandler {
	private static Pattern requestPattern = Pattern.compile("^/Applications/Deployed/(\\S*)$");
	private final Map<String, Application> deployedApps;
	private ApplicationListener applicationListener;

	public ApplicationService(Map<String, Application> deployedApps, ApplicationListener applicationListener) {
		this.deployedApps = deployedApps;
		this.applicationListener = applicationListener;
	}

	public void handle(HttpExchange he) throws IOException {
		String method = he.getRequestMethod();

		if ("POST".equals(method)) {
			Matcher requestMatcher = requestPattern.matcher(he.getRequestURI().getPath());
			if (requestMatcher.matches()) {
				String applicationName = requestMatcher.group(1);
				Application application;

				synchronized (deployedApps) {
					application = deployedApps.get(applicationName);
				}

				if (application != null) {
					synchronized (application) {
						application.setAvailable(true);
					}
					he.sendResponseHeaders(200, 0);
					he.close();
					try {
						applicationListener.addDeployedApplication(application, ApplicationServerImplementation.getInstance());
					} catch (RemoteException ex) {
						Logger.getLogger(ApplicationService.class.getName()).log(Level.SEVERE, ex.getMessage(), ex);
					}

				} else {
					he.sendResponseHeaders(500, 0);
					he.close();
				}
			} else {
				System.out.println("bad request");
				System.out.println(he.getRequestURI().getPath());
				he.sendResponseHeaders(400, 0);
				he.close();
			}
		} else if ("DELETE".equals(method)) {
			Matcher requestMatcher = requestPattern.matcher(he.getRequestURI().getPath());
			if (requestMatcher.matches()) {
				String applicationName = requestMatcher.group(1);
				Application application;
				synchronized (deployedApps) {
					application = deployedApps.remove(applicationName);
				}
				if (application != null) {
					he.sendResponseHeaders(200, 0);
					he.close();
					applicationListener.removeDeployedApplication(application, ApplicationServerImplementation.getInstance());
				} else {
					he.sendResponseHeaders(500, 0);
					he.close();
				}
				System.out.println(method);
				System.out.println(requestMatcher.group(1));

			} else {
				System.out.println("bad request");
				System.out.println(he.getRequestURI().getPath());
				he.sendResponseHeaders(400, 0);
				he.close();
			}
		} else {
			he.sendResponseHeaders(405, 0);
			he.close();
		}
	}
}
