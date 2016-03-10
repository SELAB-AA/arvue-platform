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
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.Observable;

/**
 *
 * @author bbyholm
 */
public class ArvueRegistry extends Observable implements ArvueRegistryInf {
	private static final long serialVersionUID = 5664519758239316821L;
	private final Map<String, Remote> bindings = Collections.synchronizedMap(new HashMap<String, Remote>(128));

	public Remote lookup(String name) throws RemoteException, NotBoundException, AccessException {
		synchronized (bindings) {
			Remote remote = bindings.get(name);

			if (remote == null) {
				throw new NotBoundException(name);
			}

			return remote;
		}
	}

	public void bind(String name, Remote remote) throws RemoteException, AlreadyBoundException, AccessException {
		synchronized (bindings) {
			if (bindings.get(name) != null) {
				throw new AlreadyBoundException(name);
			}

			bindings.put(name, remote);
			setChanged();
			notifyObservers(new RegistryChange(RegistryChange.Event.BIND, name, remote));
		}
	}

	public void unbind(String name) throws RemoteException, NotBoundException, AccessException {
		synchronized (bindings) {
			if (bindings.get(name) == null) {
				throw new NotBoundException(name);
			}

			bindings.remove(name);
			setChanged();
			notifyObservers(new RegistryChange(RegistryChange.Event.UNBIND, name, null));
		}
	}

	public void rebind(String name, Remote remote) throws RemoteException, AccessException {
		bindings.put(name, remote);
		setChanged();
		notifyObservers(new RegistryChange(RegistryChange.Event.REBIND, name, remote));
	}

	public String[] list() throws RemoteException, AccessException {
		String[] names;
		synchronized (bindings) {
			names = new String[bindings.size()];
			return bindings.keySet().toArray(names);
		}
	}

	public int size() {
		return bindings.size();
	}
}
