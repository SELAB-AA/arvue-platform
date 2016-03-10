/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.registry;

import java.rmi.Remote;

/**
 *
 * @author bbyholm
 */
public class RegistryChange {
	public static enum Event {
		BIND,
		UNBIND,
		REBIND
	};

	private Event event;
	private String name;
	private Remote remote;

	public RegistryChange(Event event, String name, Remote remote) {
		if (event == null) {
			throw new IllegalArgumentException("event cannot be null");
		}

		if (name == null) {
			throw new IllegalArgumentException("name cannot be null");
		}

		this.event = event;
		this.name = name;
		this.remote = remote;
	}

	/**
	 * @return the event
	 */
	public Event getEvent() {
		return event;
	}

	/**
	 * @return the name
	 */
	public String getName() {
		return name;
	}

	/**
	 * @return the remote
	 */
	public Remote getRemote() {
		return remote;
	}

	@Override
	public String toString() {
		StringBuilder sb = new StringBuilder(event.name()).append(' ').append(getName());

		if (getRemote() != null) {
			sb.append(' ');
			sb.append(getRemote());
		}

		return sb.toString();
	}
}
