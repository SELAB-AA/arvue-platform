/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.application.server;

import java.rmi.Remote;
import java.rmi.RemoteException;
import org.vaadin.arvue.application.ApplicationStatus;
import org.vaadin.arvue.application.repository.ApplicationRepositoryException;
import org.vaadin.arvue.application.repository.ApplicationRepositoryFactory;

/**
 *
 * @author User
 */
public interface ApplicationServer extends Remote {
	public String getName() throws RemoteException;
	public int getPort() throws RemoteException;
	public String getPublicAddress() throws RemoteException;
	public String getPrivateAddress() throws RemoteException;
	public String[] getDeployedApps() throws RemoteException;
	public void deploy(String appName)
			throws RemoteException, DeploymentException;
    public void deploy(String appName, String version)
			throws RemoteException, DeploymentException;
    public void undeploy(String appName)
			throws RemoteException, DeploymentException;
    public void undeploy(String appName, String version)
			throws RemoteException, DeploymentException;
    public ServerStatus status() throws RemoteException, PerformanceException;
    public void setRepositoryFactory(ApplicationRepositoryFactory repository) throws RemoteException, ApplicationRepositoryException;
	public String getDeployPath() throws RemoteException;
	public void setDeployPath(String aDeployPath) throws RemoteException;
	public void addResponseTime(String applicationName, int responseTime) throws RemoteException, DeploymentException;
	public String getInstanceID() throws RemoteException;
	public ApplicationStatus[] applicationStatus() throws RemoteException;
}
