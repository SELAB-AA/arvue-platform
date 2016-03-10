/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.application.listener;

import com.google.common.collect.HashMultimap;
import com.google.common.collect.Multimaps;
import com.google.common.collect.SetMultimap;
import java.rmi.AccessException;
import java.rmi.NotBoundException;
import java.rmi.RemoteException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.logging.Level;
import java.util.logging.Logger;
import org.vaadin.arvue.application.Application;
import org.vaadin.arvue.application.server.ApplicationServer;
import org.vaadin.arvue.loadbalancer.LoadBalancer;
import org.vaadin.arvue.registry.ArvueRegistry;

/**
 *
 * @author bbyholm
 */
public class ApplicationListenerImplementation implements ApplicationListener {
	private final SetMultimap<Application, ApplicationServer> deployedApplications;
	private final Set<Application> pendingApplications;
	private final LoadBalancer loadBalancer;
	private final ArvueRegistry appServerRegistry;
	private final Map<String, Application> applicationMap;

	public ApplicationListenerImplementation(LoadBalancer loadBalancer, ArvueRegistry appServerRegistry) {
		deployedApplications = Multimaps.synchronizedSetMultimap(HashMultimap.<Application, ApplicationServer>create());
		pendingApplications = Collections.synchronizedSet(new HashSet<Application>());
		this.loadBalancer = loadBalancer;
		this.appServerRegistry = appServerRegistry;
		applicationMap = Collections.synchronizedMap(new HashMap<String, Application>());
	}

	public void addDeployedApplication(Application application, ApplicationServer applicationServer) throws RemoteException {
		Set<ApplicationServer> servers;

		synchronized (applicationMap) {
			applicationMap.put(application.getName(), application);
		}

		servers = deployedApplications.get(application);

		synchronized (deployedApplications) {
			if (applicationServer != null) {
				servers.add(applicationServer);
			}
		}


		synchronized (pendingApplications) {
			pendingApplications.remove(application);
		}

		ArrayList<ApplicationServer> list = new ArrayList<ApplicationServer>();

		for (String name : appServerRegistry.list()) {
			try {
				list.add((ApplicationServer) appServerRegistry.lookup(name));
			} catch (NotBoundException ex) {
				Logger.getLogger(ApplicationListenerImplementation.class.getName()).log(Level.SEVERE, null, ex);
			} catch (AccessException ex) {
				Logger.getLogger(ApplicationListenerImplementation.class.getName()).log(Level.SEVERE, null, ex);
			}
		}

		if (loadBalancer != null) {
			loadBalancer.configure(list, pendingApplications);
			loadBalancer.restart();
		}
	}

	public void removeDeployedApplication(Application application, ApplicationServer applicationServer) throws RemoteException {
		Set<ApplicationServer> servers;

		synchronized (applicationMap) {
			applicationMap.remove(application.getName());
		}

		synchronized (deployedApplications) {
			servers = deployedApplications.get(application);
		}
		if (servers == null) {
			throw new RemoteException("Servers was null.");
		}

		synchronized (servers) {
			servers.remove(applicationServer);
		}
	}

	public void addPendingApplication(Application application) throws RemoteException {
		synchronized (pendingApplications) {
			pendingApplications.add(application);
		}
	}

	public void removePendingApplication(Application application) throws RemoteException {
		synchronized (pendingApplications) {
			pendingApplications.remove(application);
		}
	}

	public SetMultimap<Application, ApplicationServer> getDeployedApplications() throws RemoteException {
		return deployedApplications;
	}

	public Set<Application> getPendingApplications() throws RemoteException {
		return pendingApplications;
	}

	public Map<String, Application> getDeployedApplicationMap() throws RemoteException {
		return applicationMap;
	}

}
