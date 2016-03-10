/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.application.listener;

import com.google.common.collect.SetMultimap;
import java.rmi.Remote;
import java.rmi.RemoteException;
import java.util.Map;
import java.util.Set;
import org.vaadin.arvue.application.Application;
import org.vaadin.arvue.application.server.ApplicationServer;

/**
 *
 * @author bbyholm
 */
public interface ApplicationListener extends Remote {
	public void addDeployedApplication(Application application, ApplicationServer applicationServer) throws RemoteException;
	public void removeDeployedApplication(Application application, ApplicationServer applicationServer) throws RemoteException;
	public void addPendingApplication(Application application) throws RemoteException;
	public void removePendingApplication(Application application) throws RemoteException;
	public SetMultimap<Application, ApplicationServer> getDeployedApplications() throws RemoteException;
	public Set<Application> getPendingApplications() throws RemoteException;
	public Map<String, Application> getDeployedApplicationMap() throws RemoteException;
}
