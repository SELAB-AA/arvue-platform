/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.instance.manager;

import com.amazonaws.AmazonClientException;
import com.amazonaws.AmazonServiceException;
import com.amazonaws.auth.AWSCredentials;
import com.amazonaws.services.ec2.AmazonEC2;
import com.amazonaws.services.ec2.AmazonEC2Client;
import com.amazonaws.services.ec2.model.AuthorizeSecurityGroupIngressRequest;
import com.amazonaws.services.ec2.model.CreateSecurityGroupRequest;
import com.amazonaws.services.ec2.model.Instance;
import com.amazonaws.services.ec2.model.RunInstancesRequest;
import com.amazonaws.services.ec2.model.RunInstancesResult;
import com.amazonaws.services.ec2.model.TerminateInstancesRequest;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.URL;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Set;
import java.util.logging.Level;
import java.util.logging.Logger;
import org.vaadin.arvue.instance.EC2InstanceAdapter;
import org.vaadin.arvue.instance.InstanceException;
import org.vaadin.arvue.instance.ServerInstance;
import sun.misc.BASE64Encoder;

/**
 *
 * @author bbyholm
 */
public class EC2InstanceManager extends AbstractInstanceManager {
	private AmazonEC2 ec2Client;
	private String securityGroup;
	private String masterLocalAddress;
	private String masterPublicAddress;
	private static final int MAX_INSTANCES = 20;
	private static int instance_count = 0;

	public EC2InstanceManager(AWSCredentials credentials) {
		BufferedReader reader = null;
		ec2Client = new AmazonEC2Client(credentials);
		ec2Client.setEndpoint("ec2.eu-west-1.amazonaws.com");

		securityGroup = "arvue";

		boolean ec2 = false;

		try {
			reader = new BufferedReader(new InputStreamReader(new URL("http://169.254.169.254/latest/meta-data/local-ipv4").openStream()));
			masterLocalAddress = reader.readLine();
			reader.close();
			reader = new BufferedReader(new InputStreamReader(new URL("http://169.254.169.254/latest/meta-data/public-ipv4").openStream()));
			masterPublicAddress = reader.readLine();
			reader.close();
			ec2 = true;
			Logger.getLogger(EC2InstanceManager.class.getName()).log(Level.INFO, "masterLocalAddress : {0}", masterLocalAddress);
			Logger.getLogger(EC2InstanceManager.class.getName()).log(Level.INFO, "masterPublicAddress : {0}", masterPublicAddress);
		} catch (IOException ex) {
			Logger.getLogger(EC2InstanceManager.class.getName()).log(Level.INFO, "Not running on ec2.");
		} finally {
			try {
				if (reader != null) {
					reader.close();
				}
			} catch (IOException ex) {
				Logger.getLogger(EC2InstanceManager.class.getName()).log(Level.SEVERE, null, ex);
			}
		}

		if (!ec2) {
			try {
				reader = new BufferedReader(new InputStreamReader(new URL("http://automation.whatismyip.com/n09230945.asp").openStream()));
				masterLocalAddress = reader.readLine();
				reader.close();
				masterPublicAddress = masterLocalAddress;
				Logger.getLogger(EC2InstanceManager.class.getName()).log(Level.INFO, "masterLocalAddress : {0}", masterLocalAddress);
				Logger.getLogger(EC2InstanceManager.class.getName()).log(Level.INFO, "masterPublicAddress : {0}", masterPublicAddress);
			} catch (IOException ex) {
				Logger.getLogger(EC2InstanceManager.class.getName()).log(Level.SEVERE, "Error getting ip address.");
				throw new RuntimeException(ex.getMessage(), ex);
			} finally {
				try {
					if (reader != null) {
						reader.close();
					}
				} catch (IOException ex) {
					Logger.getLogger(EC2InstanceManager.class.getName()).log(Level.SEVERE, null, ex);
				}
			}
		}

		try {
			CreateSecurityGroupRequest rq = new CreateSecurityGroupRequest(securityGroup, "appserver");
			ec2Client.createSecurityGroup(rq);
		} catch (AmazonServiceException ex) {
			Logger.getLogger(EC2InstanceManager.class.getName()).log(Level.WARNING, ex.getMessage(), ex);
		} catch (AmazonClientException ex) {
			Logger.getLogger(EC2InstanceManager.class.getName()).log(Level.WARNING, ex.getMessage(), ex);
		}


		try {
			AuthorizeSecurityGroupIngressRequest rq = new AuthorizeSecurityGroupIngressRequest();
			rq.setGroupName(securityGroup);
			rq.setFromPort(9999);
			rq.setToPort(9999);
			rq.setIpProtocol("tcp");
			rq.setCidrIp(new StringBuilder(masterLocalAddress).append("/32").toString());
			ec2Client.authorizeSecurityGroupIngress(rq);
		} catch (AmazonServiceException ex) {
			Logger.getLogger(EC2InstanceManager.class.getName()).log(Level.WARNING, ex.getMessage(), ex);
		} catch (AmazonClientException ex) {
			Logger.getLogger(EC2InstanceManager.class.getName()).log(Level.WARNING, ex.getMessage(), ex);
		}

		try {
			AuthorizeSecurityGroupIngressRequest rq = new AuthorizeSecurityGroupIngressRequest();
			rq.setGroupName(securityGroup);
			rq.setFromPort(3002);
			rq.setToPort(3002);
			rq.setIpProtocol("tcp");
			rq.setCidrIp(new StringBuilder(masterLocalAddress).append("/32").toString());
			ec2Client.authorizeSecurityGroupIngress(rq);
		} catch (AmazonServiceException ex) {
			Logger.getLogger(EC2InstanceManager.class.getName()).log(Level.WARNING, ex.getMessage(), ex);
		} catch (AmazonClientException ex) {
			Logger.getLogger(EC2InstanceManager.class.getName()).log(Level.WARNING, ex.getMessage(), ex);
		}
	}

	public void addInstance() throws InstanceException {
		addInstance(1);
	}

	public void addInstance(int count) throws InstanceException {
		if (count < 1) {
			return;
		}

		if (count + instance_count > MAX_INSTANCES) {
			throw new InstanceException("Not adding more instances, as it would exceed the current limit of " + MAX_INSTANCES + " instances.");
		}

		RunInstancesRequest rq = new RunInstancesRequest();
		rq.setImageId("ami-46f4c232");
		rq.setInstanceType("m1.small");
		rq.setKeyName("gsg-keypair");
		rq.setMaxCount(count);
		rq.setMinCount(count);
		rq.setSecurityGroups(Arrays.asList(securityGroup));
		rq.setUserData(new BASE64Encoder().encode(masterLocalAddress.getBytes()));

		try {
			RunInstancesResult result = ec2Client.runInstances(rq);
			if (result != null) {
				for (Instance ec2Instance : result.getReservation().getInstances()) {
					instances.add(new EC2InstanceAdapter(ec2Instance));
				}
			}
		} catch (AmazonServiceException ex) {
			throw new InstanceException(ex.getMessage(), ex);
		} catch (AmazonClientException ex) {
			throw new InstanceException(ex.getMessage(), ex);
		}

	}

	public void removeInstance(ServerInstance instance) throws InstanceException {
		try {
			ec2Client.terminateInstances(new TerminateInstancesRequest(Arrays.asList(instance.getInstanceId())));
			if (!instances.remove(instance)) {
				throw new InstanceException("Instance " + instance.getInstanceId() + " was not removed properly.");
			}
		} catch (AmazonServiceException ex) {
			throw new InstanceException(ex.getMessage(), ex);
		} catch (AmazonClientException ex) {
			throw new InstanceException(ex.getMessage(), ex);
		}
	}

	public void removeInstances(Set<ServerInstance> instances) throws InstanceException {
		try {
			ArrayList<String> instanceIDs = new ArrayList<String>(instances.size());
			for (ServerInstance instance : instances) {
				instanceIDs.add(instance.getInstanceId());
			}
			ec2Client.terminateInstances(new TerminateInstancesRequest(instanceIDs));
			if (!this.instances.removeAll(instances)) {
				throw new InstanceException("Instances were not removed properly.");
			}
		} catch (AmazonServiceException ex) {
			throw new InstanceException(ex.getMessage(), ex);
		} catch (AmazonClientException ex) {
			throw new InstanceException(ex.getMessage(), ex);
		}
	}

}
