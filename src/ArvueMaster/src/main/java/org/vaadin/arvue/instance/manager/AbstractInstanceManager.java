/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.instance.manager;

import java.util.Collections;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import org.vaadin.arvue.instance.InstanceException;
import org.vaadin.arvue.instance.ServerInstance;

/**
 *
 * @author bbyholm
 */
public abstract class AbstractInstanceManager {
	protected final Set<ServerInstance> instances = Collections.newSetFromMap(new ConcurrentHashMap<ServerInstance, Boolean>());

	public abstract void addInstance() throws InstanceException;
	public abstract void removeInstance(ServerInstance instance) throws InstanceException;

	public Set<ServerInstance> listInstances() {
		return Collections.unmodifiableSet(instances);
	}

}
