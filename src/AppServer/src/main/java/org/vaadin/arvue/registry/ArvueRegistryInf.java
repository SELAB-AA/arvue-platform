/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.registry;

import java.rmi.AccessException;
import java.rmi.AlreadyBoundException;
import java.rmi.NotBoundException;
import java.rmi.Remote;
import java.rmi.RemoteException;

/**
 *
 * @author bbyholm
 */
public interface ArvueRegistryInf extends Remote {
	public Remote lookup(String name) throws RemoteException, NotBoundException, AccessException;
	public void bind(String name, Remote remote) throws RemoteException, AlreadyBoundException, AccessException;
	public void unbind(String name) throws RemoteException, NotBoundException, AccessException;
	public void rebind(String name, Remote remote) throws RemoteException, AccessException;
	public String[] list() throws RemoteException, AccessException;
}
