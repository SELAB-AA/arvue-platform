/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.instance;

import com.amazonaws.services.ec2.model.Instance;

/**
 *
 * @author bbyholm
 */
public class EC2InstanceAdapter implements ServerInstance {
	Instance ec2Instance;

	public EC2InstanceAdapter(Instance ec2Instance) {
		this.ec2Instance = ec2Instance;
	}

	public String getInstanceId() {
		return ec2Instance.getInstanceId();
	}
}
