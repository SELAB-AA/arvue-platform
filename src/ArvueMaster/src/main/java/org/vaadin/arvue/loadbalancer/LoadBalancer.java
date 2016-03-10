/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.loadbalancer;

import java.util.Collection;
import org.vaadin.arvue.application.Application;
import org.vaadin.arvue.application.server.ApplicationServer;

/**
 *
 * @author bbyholm
 */
public interface LoadBalancer {
	public void start();
	public void stop();
	public void restart();
	public void configure(Collection<ApplicationServer> applicationServers);
	public void configure(Collection<ApplicationServer> applicationServers, Collection<Application> pendingApplications);
}
