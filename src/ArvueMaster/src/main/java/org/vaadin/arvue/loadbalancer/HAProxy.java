/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.loadbalancer;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.rmi.RemoteException;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.Map;

import java.util.logging.Level;
import java.util.logging.Logger;
import org.apache.velocity.Template;
import org.apache.velocity.VelocityContext;
import org.apache.velocity.app.VelocityEngine;
import org.apache.velocity.runtime.RuntimeConstants;
import org.apache.velocity.runtime.resource.loader.ClasspathResourceLoader;
import org.vaadin.arvue.application.Application;
import org.vaadin.arvue.application.server.ApplicationServer;
import org.vaadin.arvue.application.server.PerformanceException;
import org.vaadin.arvue.master.ArvueMaster;

/**
 *
 * @author bbyholm
 */
public class HAProxy implements LoadBalancer {

	/*private Collection<String> entertainmentBackendNames;

	public HAProxy() {
		entertainmentBackendNames = new ArrayList<String>(1);
		entertainmentBackendNames.add("entertainment_1");
	}*/

	@SuppressWarnings("SleepWhileInLoop")
	public void start() {
		File processFile = new File("/tmp/haproxy.pid");
		File configurationFile = new File("/tmp/haproxy.conf");

		if (processFile.exists()) {
			throw new RuntimeException("/tmp/haproxy.pid already exists");
		}

		if (!configurationFile.exists()) {
			throw new RuntimeException("/tmp/haproxy.conf does not exist");
		}

		try {
			Process p = Runtime.getRuntime().exec("/usr/sbin/haproxy -f /tmp/haproxy.conf -p /tmp/haproxy.pid");
			int countdown = 10;
			while (countdown-- > 0) {
				try {
					if (p.exitValue() == 0) {
						Runtime.getRuntime().addShutdownHook(
							new Thread() {
								@Override
									public void run() {
										System.out.println("Stoping loadbalancer...");
										HAProxy.this.stop();
									}
								}
						);
						return;
					} else {
						throw new RuntimeException("Error starting haproxy! - Errorexit");
					}
				} catch (IllegalThreadStateException ex) {
					try {
						Thread.sleep(100);
					} catch (InterruptedException e) {
						Thread.currentThread().interrupt();
					}
				}
			}

			//timeout

			throw new RuntimeException("Error starting haproxy! - Timeout");

		} catch (IOException ex) {
			throw new RuntimeException(ex.getMessage(), ex);
		}
	}

	public void stop() {

		BufferedReader reader;
		try {
			File f = new File("/tmp/haproxy.pid");
			reader = new BufferedReader(new FileReader(f));
			try {
				boolean anythingToKill = false;
				StringBuilder sb = new StringBuilder("/usr/bin/kill");
				String line;
				while ((line = reader.readLine()) != null) {
					anythingToKill = true;
					sb.append(' ').append(line);
				}

				if (anythingToKill) {
					Runtime.getRuntime().exec(sb.toString());
				}
			} finally {
				reader.close();
			}
			f.delete();
		} catch (IOException ex) {
			Logger.getLogger(HAProxy.class.getName()).log(Level.SEVERE, null, ex);
		}



	}

	public void restart() {
		File confFile = new File("/tmp/haproxy.conf");
		if (!confFile.exists()) {
			throw new RuntimeException("/tmp/haproxy.conf doesn't exist");
		}

		File pidFile = new File("/tmp/haproxy.pid");
		if (!pidFile.exists()) {
			throw new RuntimeException("/tmp/haproxy.pid doesn't exist");
		}

		try {
			BufferedReader reader = new BufferedReader(new FileReader("/tmp/haproxy.pid"));
			String line = reader.readLine();

			StringBuilder sb = new StringBuilder("/usr/sbin/haproxy -f /tmp/haproxy.conf -p /tmp/haproxy.pid");
			if (line != null && !line.isEmpty()) {
				sb.append(" -sf ").append(line);
			}
			while ((line = reader.readLine()) != null) {
				sb.append(' ').append(line);
			}
			Runtime.getRuntime().exec(sb.toString());
		} catch (IOException ex) {
			throw new RuntimeException(ex.getMessage(), ex);
		}
	}

	public void configure(Collection<ApplicationServer> applicationServers) {
		configure(applicationServers, null);
	}

	public void configure(Collection<ApplicationServer> applicationServers, Collection<Application> pendingApplications) {
		if (applicationServers == null) {
			throw new IllegalArgumentException("applicationServers may not be null");
		}

		Map<String, Collection<ApplicationServer>> usage = new HashMap<String, Collection<ApplicationServer>>();
		Map<ApplicationServer, Float> loadMap = new HashMap<ApplicationServer, Float>();
		Map<ApplicationServer, Integer> weightMap = new HashMap<ApplicationServer, Integer>();
		float loadSum = 0;
		float loadMax = 0;

		StringBuilder backendStringBuilder = new StringBuilder();
		StringBuilder aclStringBuilder = new StringBuilder();
		StringBuilder usageStringBuilder = new StringBuilder();

		for (ApplicationServer applicationServer : applicationServers) {
			try {
				float load = applicationServer.status().getCpuLoad();
				loadMax = loadMax < load ? load : loadMax;
				loadSum += load;
				loadMap.put(applicationServer, load);

				String[] deployedApplications = applicationServer.getDeployedApps();
				for (String application : deployedApplications) {
					Collection<ApplicationServer> backendCollection = usage.get(application);

					if (backendCollection == null) {
						backendCollection = new ArrayList<ApplicationServer>();
						usage.put(application, backendCollection);
					}

					backendCollection.add(applicationServer);
				}
			} catch (RemoteException ex) {
				Logger.getLogger(HAProxy.class.getName()).log(Level.SEVERE, null, ex);
			} catch (PerformanceException ex) {
				Logger.getLogger(HAProxy.class.getName()).log(Level.SEVERE, null, ex);
			}
		}

		for (ApplicationServer applicationServer : applicationServers) {
			if (loadMap.get(applicationServer) >= ArvueMaster.CPU_LIMIT_HIGH) {
				weightMap.put(applicationServer, 1);
			} else if (loadMap.get(applicationServer) > 0) {
				weightMap.put(applicationServer, (int) Math.round(256 - loadMap.get(applicationServer) / ArvueMaster.CPU_LIMIT_HIGH * (256 - 1)));
			} else {
				weightMap.put(applicationServer, 100);
			}
		}

		for (String applicationName : usage.keySet()) {
			backendStringBuilder
					.append("\tbackend ")
					.append(applicationName)
					.append(System.getProperty("line.separator"));
			for (ApplicationServer backend : usage.get(applicationName)) {
				try {
					backendStringBuilder
							.append("\t\tserver ")
							.append(backend.getName())
							.append(' ')
							.append(backend.getPrivateAddress())
							.append(':')
							.append(backend.getPort())
							.append(' ')
							.append("cookie")
							.append(' ')
							.append(backend.getName())
							.append(' ')
							.append("weight")
							.append(' ')
							.append(weightMap.get(backend))
							.append(System.getProperty("line.separator"));
				} catch (RemoteException ex) {
					Logger.getLogger(HAProxy.class.getName()).log(Level.SEVERE, ex.getMessage(), ex);
				}
			}



			aclStringBuilder
					.append("\tacl acl_")
					.append(applicationName)
					.append(" path_beg /")
					.append(applicationName)
					.append(System.getProperty("line.separator"));

			usageStringBuilder
					.append("\tuse_backend ")
					.append(applicationName)
					.append(" if acl_")
					.append(applicationName)
					.append(System.getProperty("line.separator"));
		}

		if (pendingApplications != null) {
			for (Application application : pendingApplications) {
				aclStringBuilder
						.append("\tacl acl_")
						.append(application.getName())
						.append(" path_beg /")
						.append(application.getName())
						.append(System.getProperty("line.separator"));

				usageStringBuilder
						.append("\tuse_backend ")
						.append("entertainment")
						.append(" if acl_")
						.append(application.getName())
						.append(System.getProperty("line.separator"));
			}
		}

		VelocityEngine ve = new VelocityEngine();
		ve.setProperty(RuntimeConstants.RESOURCE_LOADER, "classpath");
		ve.setProperty("classpath.resource.loader.class", ClasspathResourceLoader.class.getName());
		try {
			ve.init();
			Template t = ve.getTemplate("haproxy.conf", "UTF-8");
			VelocityContext context = new VelocityContext();
			context.put("listen_port", 8088);
			context.put("arvue_port", 8080);
			context.put("backends", backendStringBuilder.toString());
			context.put("acl", aclStringBuilder.toString());
			context.put("backenduse", usageStringBuilder.toString());

			BufferedWriter writer = new BufferedWriter(new FileWriter("/tmp/haproxy.conf"));
			try {
				t.merge(context, writer);
			} finally {
				writer.close();
			}
		} catch (Exception ex) {
			Logger.getLogger(HAProxy.class.getName()).log(Level.SEVERE, null, ex);
		}

	}

}
