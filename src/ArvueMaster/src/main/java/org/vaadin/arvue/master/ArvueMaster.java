/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.master;

import com.amazonaws.auth.BasicAWSCredentials;
import com.google.common.collect.HashMultimap;
import com.google.common.collect.Multimaps;
import com.google.common.collect.SetMultimap;
import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintStream;
import java.net.ServerSocket;
import java.net.Socket;
import java.rmi.AccessException;
import java.rmi.AlreadyBoundException;
import java.rmi.NotBoundException;
import java.rmi.Remote;
import java.rmi.RemoteException;
import java.rmi.registry.LocateRegistry;
import java.rmi.registry.Registry;
import java.rmi.server.UnicastRemoteObject;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.Date;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Map;
import java.util.Observable;
import java.util.Observer;
import java.util.PriorityQueue;
import java.util.Random;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.apache.commons.io.FileUtils;
import org.vaadin.arvue.application.Application;
import org.vaadin.arvue.application.ApplicationStatus;
import org.vaadin.arvue.application.listener.ApplicationListener;
import org.vaadin.arvue.application.listener.ApplicationListenerImplementation;
import org.vaadin.arvue.application.repository.ApplicationRepository;
import org.vaadin.arvue.application.repository.ApplicationRepositoryException;
import org.vaadin.arvue.application.repository.ApplicationRepositoryFactory;
import org.vaadin.arvue.application.repository.S3ApplicationRepositoryFactory;
import org.vaadin.arvue.application.server.ApplicationServer;
import org.vaadin.arvue.application.server.DeploymentException;
import org.vaadin.arvue.application.server.PerformanceException;
import org.vaadin.arvue.application.server.ServerStatus;
import org.vaadin.arvue.instance.InstanceException;
import org.vaadin.arvue.instance.ServerInstance;
import org.vaadin.arvue.instance.manager.EC2InstanceManager;
import org.vaadin.arvue.loadbalancer.HAProxy;
import org.vaadin.arvue.loadbalancer.LoadBalancer;
import org.vaadin.arvue.loadbalancer.listener.LoadBalancerListener;
import org.vaadin.arvue.registry.ArvueRegistry;
import org.vaadin.arvue.registry.ArvueRegistryInf;
import org.vaadin.arvue.registry.RegistryChange;

/**
 *
 * @author User
 */
public class ArvueMaster implements Observer {
	private static ArvueMaster instance;
	private static final Registry serviceRegistry;
	private static final ArvueRegistry appServerRegistry;
	private static final ApplicationRepositoryFactory applicationRepositoryFactory;
	private static final ApplicationRepository applicationRepository;
	private static final Provisioner provisioner;
	private static final LoadBalancer loadBalancer;
	private static final ApplicationListener applicationListener;
	private static final EC2InstanceManager instanceManager;
	private static final LoadBalancerListener loadBalancerListener;
	private static final Set<ApplicationServer> nonSaturatedServers;
	private static final Set<ApplicationServer> saturatedServers;
	private static final Map<ApplicationServer, Integer> idleServers;
	private static final Set<ApplicationServer> permanentlyIdleServers;
	private static final Set<String> saturatedApplications;
	private static final Map<String, Integer> idleApplications;
	//private static final Set<String> permanentlyIdleApplications;
	private static final SetMultimap<ApplicationServer, String> serversWithSaturatedApps;

	private static int lastSaturatedServerCount = 0;
	private static int lastPermanentlyIdleCount = 0;
	private static int currentPermanentlyIdleCount = 0;

	public static final double AGGRESSIVENESS = 0.2;
	public static final double PDWEIGHT = 0.5;
	public static final double AGGRESSIVENESS_PROVISIONING = 1.0;
	public static final double AGGRESSIVENESS_TERMINATION = 1.0;

	public static final double CPU_LIMIT_LOW = 0.2;
	public static final double CPU_LIMIT_HIGH = 0.7;
	public static final double MEM_LIMIT_LOW = 0.2;
	public static final double MEM_LIMIT_HIGH = 0.8;
	public static final double APP_MEM_LIMIT_LOW = 0.01;
	public static final double APP_MEM_LIMIT_HIGH = 0.80;
	public static final int PERMANENTLY_IDLE_LIMIT = 5;
	public static final int APP_PERMANENTLY_IDLE_LIMIT = 5;
	public static final int BASE_CAPACITY = 1;

	private static final AtomicInteger serversToWaitFor = new AtomicInteger(0);

	static {
		instanceManager = new EC2InstanceManager(new BasicAWSCredentials(System.getProperty("AWSAccessKey"), System.getProperty("AWSPrivateKey")));
		applicationRepositoryFactory = new S3ApplicationRepositoryFactory(
		                                   "arvue-repo",
		                                   System.getProperty("accessKey"),
		                                   System.getProperty("privateKey")
		                               );

		provisioner = Provisioner.getInstance();
		loadBalancer = new HAProxy();

		try {
			applicationRepository = applicationRepositoryFactory.getRepository();

			serviceRegistry = LocateRegistry.createRegistry(1099);
			appServerRegistry = new ArvueRegistry();

			ArvueRegistryInf registryStub = (ArvueRegistryInf) UnicastRemoteObject.exportObject(appServerRegistry, 0);
			serviceRegistry.bind("AppServerRegistry", registryStub);

			applicationListener = new ApplicationListenerImplementation(loadBalancer, appServerRegistry);
			ApplicationListener applicationListenerStub = (ApplicationListener) UnicastRemoteObject.exportObject(applicationListener, 0);
			serviceRegistry.bind("ApplicationListener", applicationListenerStub);

			loadBalancerListener = new LoadBalancerListener(applicationListener, appServerRegistry);
			saturatedServers = new HashSet<ApplicationServer>();
			nonSaturatedServers = new HashSet<ApplicationServer>();
			idleServers = new HashMap<ApplicationServer, Integer>();
			permanentlyIdleServers = new HashSet<ApplicationServer>();
			saturatedApplications = new HashSet<String>();
			idleApplications = new HashMap<String, Integer>();
			//permanentlyIdleApplications = new HashSet<String>();
			serversWithSaturatedApps = Multimaps.synchronizedSetMultimap(HashMultimap.<ApplicationServer, String>create());
		} catch (ApplicationRepositoryException ex) {
			throw new RuntimeException(ex.getMessage(), ex);
		} catch (AlreadyBoundException ex) {
			throw new RuntimeException(ex.getMessage(), ex);
		} catch (AccessException ex) {
			throw new RuntimeException(ex.getMessage(), ex);
		} catch (RemoteException ex) {
			throw new RuntimeException(ex.getMessage(), ex);
		}
	}

	/**
	 * @return the instance
	 */
	public static ArvueMaster getInstance() {
		if (instance == null) {
			instance = new ArvueMaster();
		}

		return instance;
	}

	private ArvueMaster() {
		if (System.getSecurityManager() == null) {
			System.setProperty("java.security.policy", getClass().getClassLoader().getResource("arvuemaster.policy").toString());
			System.setSecurityManager(new SecurityManager());
		}
	}

    /**
     * @param args the command line arguments
     */
	@SuppressWarnings("SleepWhileInLoop")
    public static void main(String[] args) {
		appServerRegistry.addObserver(getInstance());

		new Thread(provisioner).start();
		loadBalancer.configure(new HashSet<ApplicationServer>());
		loadBalancer.start();

		// add initial set of servers
		try {
			int size = BASE_CAPACITY + 1;
			System.out.println("Adding " + size + " instances.");
			instanceManager.addInstance(size);
		} catch (InstanceException ex) {
			Logger.getLogger(ArvueMaster.class.getName()).log(Level.SEVERE, null, ex);
		}

		File outputFile = new File("report.dat");
		try {
			StringBuilder sb = new StringBuilder()
					.append("Time")
					.append(';')
					.append("Servers")
					.append(';')
					.append("Sessions")
					.append(';')
					.append("RTT (ms)")
					.append(';')
					.append("Load")
					.append(System.getProperty("line.separator"));
			FileUtils.writeStringToFile(outputFile, sb.toString());
		} catch (IOException ex) {
			Logger.getLogger(ArvueMaster.class.getName()).log(Level.SEVERE, null, ex);
		}

		System.out.println("Waiting three minutes for servers to arrive and stabilize their load.");
		try {
			Thread.currentThread().sleep(3 * 60 * 1000);
		} catch (InterruptedException ex) {
			Thread.currentThread().interrupt();
		}

		while (true) {
			try {
				//while (true) {
					System.out.println(new Date());
					lastSaturatedServerCount = saturatedServers.size();
					saturatedServers.clear();
					nonSaturatedServers.clear();
					permanentlyIdleServers.clear();
					saturatedApplications.clear();
					//permanentlyIdleApplications.clear();
					double global_average_cpu_load = 0;
					int cpu_load_count = 0;
					double global_average_response_time = 0;
					int response_time_count = 0;
					for (String name : appServerRegistry.list()) {
						try {
							Remote remote = appServerRegistry.lookup(name);
							if (remote instanceof ApplicationServer) {
								ApplicationServer appServer = (ApplicationServer) remote;
								try {
									ServerStatus serverStatus = appServer.status();
									if (serverStatus == null) {
										System.out.println("*****************************************");
										System.out.println("Unable to get status for server " + name);
										System.out.println("*****************************************");
										continue;
									}
									Map<String, Float> responseTimes = serverStatus.getResponseTimes();
									if (responseTimes == null) {
										System.out.println("*****************************************");
										System.out.println("Response times were null: " + name);
										System.out.println("*****************************************");
										continue;
									}
									ApplicationStatus[] applicationStati = appServer.applicationStatus();
									if (applicationStati == null) {
										System.out.println("*****************************************");
										System.out.println("Application stati were null: " + name);
										System.out.println("*****************************************");
									} else {
										for (ApplicationStatus as : applicationStati) {
											if (as.getUtil() > APP_MEM_LIMIT_HIGH) {
												idleApplications.remove(as.getName());
												saturatedApplications.add(as.getName());
												System.out.println("Application " + as.getName() + " is saturated: " + as.getUtil());
											} else if (as.getUtil() < APP_MEM_LIMIT_LOW) {
												System.out.println("Application " + as.getName() + " is underloaded: "  + as.getUtil());
												Integer count = idleApplications.get(as.getName());
												if (count == null) {
													idleApplications.put(as.getName(), Integer.valueOf(1));
												} else {
													if (count < APP_PERMANENTLY_IDLE_LIMIT) {
														idleApplications.put(as.getName(), ++count);
													} else {
														System.out.println("AS: " + as);
														System.out.println("AS.name: " + as.getName());
														Float rt = responseTimes.get(as.getName());
														if (rt != null) {
															System.out.println("RTT(AS): " + rt.floatValue());
															if (rt.floatValue() > 0.0) {	//lame way of seeing if requests have been made
																//this is where we would have done migration
																System.out.println("Not undeploying application " + as.getName() + " from " + appServer.getName() + " due to active sessions!");
															} else {
																try {
																	System.out.println("Attempting to undeploy application " + as.getName() + " from " + appServer.getName());
																	applicationListener.removeDeployedApplication(new Application(as.getName(), null), appServer);
																	ArrayList<ApplicationServer> list = new ArrayList<ApplicationServer>();

																	for (String serverName : appServerRegistry.list()) {
																		try {
																			list.add((ApplicationServer) appServerRegistry.lookup(serverName));
																		} catch (NotBoundException ex) {
																			Logger.getLogger(ApplicationListenerImplementation.class.getName()).log(Level.SEVERE, null, ex);
																		} catch (AccessException ex) {
																			Logger.getLogger(ApplicationListenerImplementation.class.getName()).log(Level.SEVERE, null, ex);
																		}
																	}
																	loadBalancer.configure(list);
																	loadBalancer.restart();
																	appServer.undeploy(as.getName());
																} catch (DeploymentException ex) {
																	Logger.getLogger(ArvueMaster.class.getName()).log(Level.SEVERE, null, ex);
																}
																idleApplications.remove(as.getName());
															}
														}

													}
												}
											} else {
												System.out.println("Application " + as.getName() + " is alright: "  + as.getUtil());
												idleApplications.remove(as.getName());
											}
										}
									}
									float averageResponseTime = 0;
									int responseTimeCount = 0;
									for (Float responseTime : responseTimes.values()) {
										if (responseTime > 0) {
											averageResponseTime += responseTime;
											responseTimeCount++;
										}
									}

									averageResponseTime /= responseTimeCount;

									global_average_cpu_load += serverStatus.getCpuLoad();
									cpu_load_count++;

									if (averageResponseTime > 0) {
										global_average_response_time += averageResponseTime;
										response_time_count++;
									}

									if (serverStatus.getMemLoad() > MEM_LIMIT_HIGH || serverStatus.getCpuLoad() > CPU_LIMIT_HIGH) {
										System.out.println(appServer.getName() + " (" + appServer.getInstanceID() + ")" + " is overloaded.");
										System.out.println(serverStatus);

										ArrayList appList = new ArrayList();

										for (String s : appServer.getDeployedApps()) {
											if (s == null) {
												System.out.println();
												System.out.println("****************");
												System.out.println("ERROR: an appname was null");
												System.out.println("****************");
												System.out.println();
											} else {
												appList.add(s);
											}
										}

										synchronized (serversWithSaturatedApps) {
											Set s = serversWithSaturatedApps.get(appServer);
											s.addAll(appList);
											saturatedServers.add(appServer);
										}

										saturatedApplications.addAll(appList);
										idleServers.remove(appServer);
									} else if (serverStatus.getMemLoad() < MEM_LIMIT_LOW && serverStatus.getCpuLoad() < CPU_LIMIT_LOW) {
										System.out.println(appServer.getName() + " (" + appServer.getInstanceID() + ")" + " is underloaded.");
										System.out.println(serverStatus);
										Integer count = idleServers.get(appServer);
										if (count == null) {
											idleServers.put(appServer, Integer.valueOf(1));
										} else {
											idleServers.put(appServer, ++count);
										}
										nonSaturatedServers.add(appServer);
									} else {
										System.out.println(appServer.getName() + " (" + appServer.getInstanceID() + ")" + " is alright.");
										System.out.println(serverStatus);
										idleServers.remove(appServer);
										nonSaturatedServers.add(appServer);
									}
								} catch (PerformanceException ex) {
									Logger.getLogger(ArvueMaster.class.getName()).log(Level.SEVERE, null, ex);
								} catch (RemoteException ex) {
									Logger.getLogger(ArvueMaster.class.getName()).log(Level.SEVERE, null, ex);
								}
							}
						} catch (NotBoundException ex) {
							Logger.getLogger(ArvueMaster.class.getName()).log(Level.SEVERE, null, ex);
						}
					}

					if (cpu_load_count > 0) {
						global_average_cpu_load /= cpu_load_count;
					}

					if (response_time_count > 0) {
						global_average_response_time /= response_time_count;
					}

					if (saturatedServers.size() >= 1 && nonSaturatedServers.size() >= 1) {
						int size = instanceManager.listInstances().size();
						PriorityQueue<ApplicationServer> pq = new PriorityQueue<ApplicationServer>(size, new Comparator<ApplicationServer>() {
							public int compare(ApplicationServer t, ApplicationServer t1) {
								try {
									if (t.status().getCpuLoad() + t.status().getMemLoad() < t1.status().getCpuLoad() + t1.status().getMemLoad()) {
										return -1;
									} else if (t1.status().getCpuLoad() + t1.status().getMemLoad() > t.status().getCpuLoad() + t.status().getMemLoad()) {
										return 1;
									} else {
										return 0;
									}
								} catch (RemoteException ex) {
									Logger.getLogger(ArvueMaster.class.getName()).log(Level.SEVERE, null, ex);
								} catch (PerformanceException ex) {
									Logger.getLogger(ArvueMaster.class.getName()).log(Level.SEVERE, null, ex);
								}
								return 0;
							}
						});

						pq.addAll(nonSaturatedServers);

						for (String applicationName : saturatedApplications) {
							try {
								pq.peek().deploy(applicationName);
							} catch (DeploymentException ex) {
								Logger.getLogger(ArvueMaster.class.getName()).log(Level.SEVERE, null, ex);
							}
						}
					}

					try {
						StringBuilder sb = new StringBuilder()
								.append('"')
								.append(new Date())
								.append('"')
								.append(';')
								.append(appServerRegistry.size())
								.append(';')
								.append(0)
								.append(';')
								.append(global_average_response_time)
								.append(';')
								.append(global_average_cpu_load)
								.append(System.getProperty("line.separator"));
						FileUtils.writeStringToFile(outputFile, sb.toString(), true);
					} catch (IOException ex) {
						Logger.getLogger(ArvueMaster.class.getName()).log(Level.SEVERE, null, ex);
					}

					System.out.println("Global average CPU load: " + global_average_cpu_load);
					System.out.println("Global average RTT: " + global_average_response_time);
					System.out.println("saturatedServers.size: " + saturatedServers.size());
					System.out.println("appServerRegistry.size: " + appServerRegistry.size());
					System.out.println();

					if (serversToWaitFor.get() <= 0 && saturatedServers.size() >= appServerRegistry.size() - computeExtraCapacity() && computeServersToProvision() >= 1) {
						int size = computeServersToProvision();
						try {
							System.out.println("********************");
							System.out.println("Adding " + size + " instances!");
							System.out.println("********************");
							instanceManager.addInstance(size);
							serversToWaitFor.set(size);
						} catch (InstanceException ex) {
							Logger.getLogger(ArvueMaster.class.getName()).log(Level.SEVERE, null, ex);
						}
					}

					if (!idleServers.isEmpty()) {
						Iterator<ApplicationServer> it = idleServers.keySet().iterator();
						while (it.hasNext()) {
							ApplicationServer applicationServer = it.next();
							if (idleServers.get(applicationServer) >= PERMANENTLY_IDLE_LIMIT) {
								System.out.println(applicationServer.getName() + " is permanently idle");
								permanentlyIdleServers.add(applicationServer);
	//							it.remove();
							}
						}
					}


					lastPermanentlyIdleCount = currentPermanentlyIdleCount;
					currentPermanentlyIdleCount = permanentlyIdleServers.size();

					System.out.println("Last PIDLE Count: " + lastPermanentlyIdleCount);
					System.out.println("Current PIDLE Count: " + currentPermanentlyIdleCount);
					System.out.println("Extra Capacity: " + computeExtraCapacity());
					System.out.println("Servers to Terminate: " + computeServersToTerminate());

					//int size = instanceManager.listInstances().size();

					if (serversToWaitFor.get() <= 0 && permanentlyIdleServers.size() - BASE_CAPACITY - computeExtraCapacity() > 0 && computeServersToTerminate() > 0) {
						int i = computeServersToTerminate();

						PriorityQueue<ApplicationServer> pq = new PriorityQueue<ApplicationServer>(permanentlyIdleServers.size(), new Comparator<ApplicationServer>() {
							public int compare(ApplicationServer t, ApplicationServer t1) {
								try {
									if (t.status().getCpuLoad() + t.status().getMemLoad() < t1.status().getCpuLoad() + t1.status().getMemLoad()) {
										return -1;
									} else if (t1.status().getCpuLoad() + t1.status().getMemLoad() > t.status().getCpuLoad() + t.status().getMemLoad()) {
										return 1;
									} else {
										return 0;
									}
								} catch (RemoteException ex) {
									Logger.getLogger(ArvueMaster.class.getName()).log(Level.SEVERE, null, ex);
								} catch (PerformanceException ex) {
									Logger.getLogger(ArvueMaster.class.getName()).log(Level.SEVERE, null, ex);
								}
								return 0;
							}
						});

						pq.addAll(permanentlyIdleServers);

						for (String applicationName : saturatedApplications) {
							try {
								pq.peek().deploy(applicationName);
							} catch (DeploymentException ex) {
								Logger.getLogger(ArvueMaster.class.getName()).log(Level.SEVERE, null, ex);
							}
						}

						/* TODO: This is horribly inefficient, compute list of servers to terminate, then terminate them and reconfigure loadbalancer once */
						while(!pq.isEmpty() && i-- > 0) {
							ApplicationServer applicationServer = pq.poll();
							String instanceID = applicationServer.getInstanceID();
							if (instanceID != null) {
								for (ServerInstance serverInstance : instanceManager.listInstances()) {
									if (serverInstance.getInstanceId().equals(instanceID)) {
										try {
											System.out.println("***********************");
											System.out.println("Removing one instance!");
											System.out.println("***********************");
											appServerRegistry.unbind(applicationServer.getName());
											permanentlyIdleServers.remove(applicationServer);
											idleServers.remove(applicationServer);

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
											loadBalancer.configure(list);
											loadBalancer.restart();
											instanceManager.removeInstance(serverInstance);
											serversWithSaturatedApps.removeAll(applicationServer);
										} catch (NotBoundException ex) {
											Logger.getLogger(ArvueMaster.class.getName()).log(Level.SEVERE, null, ex);
										} catch (InstanceException ex) {
											Logger.getLogger(ArvueMaster.class.getName()).log(Level.SEVERE, null, ex);
										}
									}
								}
							}
						}
					}


					ArrayList<ApplicationServer> list = new ArrayList<ApplicationServer>();

					/* Reconfigure loadbalancer */

					for (String name : appServerRegistry.list()) {
						try {
							list.add((ApplicationServer) appServerRegistry.lookup(name));
						} catch (NotBoundException ex) {
							Logger.getLogger(ApplicationListenerImplementation.class.getName()).log(Level.SEVERE, null, ex);
						} catch (AccessException ex) {
							Logger.getLogger(ApplicationListenerImplementation.class.getName()).log(Level.SEVERE, null, ex);
						}
					}

					loadBalancer.configure(list);
					loadBalancer.restart();

					System.out.println();

					try {
						Thread.sleep(10 * 1000);
					} catch (InterruptedException ex) {
						Thread.currentThread().interrupt();
					}
				//}
			} catch (AccessException ex) {
				Logger.getLogger(ArvueMaster.class.getName()).log(Level.SEVERE, null, ex);
			} catch (RemoteException ex) {
				Logger.getLogger(ArvueMaster.class.getName()).log(Level.SEVERE, null, ex);
			}
		}
    }

	@Override
	public void update(Observable o, Object arg) {
		if (o instanceof ArvueRegistry && arg instanceof RegistryChange) {
			RegistryChange rc = (RegistryChange) arg;

			switch (rc.getEvent()) {
				case BIND:
					int serversLeft = serversToWaitFor.decrementAndGet();
					ApplicationServer appServer = (ApplicationServer) rc.getRemote();
					try {
						appServer.setRepositoryFactory(
							applicationRepositoryFactory
						);
						synchronized (serversWithSaturatedApps) {
							HashSet<String> appsToDeploy = new HashSet<String>();
							appsToDeploy.addAll(serversWithSaturatedApps.values());


							for (String applicationName : appsToDeploy) {
								try {
									appServer.deploy(applicationName);
								} catch (DeploymentException ex) {
									Logger.getLogger(ArvueMaster.class.getName()).log(Level.SEVERE, null, ex);
								}
							}
						}

						if (serversLeft == 0) {
							synchronized (serversWithSaturatedApps) {
								serversWithSaturatedApps.clear();
							}
						}
					} catch (RemoteException ex) {
						Logger.getLogger(ArvueMaster.class.getName()).log(Level.SEVERE, null, ex);
					} catch (ApplicationRepositoryException ex) {
						Logger.getLogger(ArvueMaster.class.getName()).log(Level.SEVERE, null, ex);
					}
			}
		}
	}

	private static int computeExtraCapacity() {
		int size = appServerRegistry.size();
		int saturatedSize = saturatedServers.size();
		int result;

		if (size == saturatedSize) {
			result = (int) Math.ceil(size * AGGRESSIVENESS);
		} else {
			result = (int) Math.ceil(((double) size) / (size - saturatedSize) * AGGRESSIVENESS);
		}
		System.out.println("computeExtraCapacity: " + result);
		return result;
	}

	private static int computeServersToProvision() {
		return (int) Math.ceil(PDWEIGHT * computeProportionalProvisioningFactor() + (1 - PDWEIGHT) * computeDerivativeProvisioningFactor());
	}

	private static double computeProportionalProvisioningFactor() {
		return saturatedServers.size() * AGGRESSIVENESS_PROVISIONING;
	}

	private static double computeDerivativeProvisioningFactor() {
		return saturatedServers.size() - lastSaturatedServerCount;
	}

	private static int computeServersToTerminate() {
		int i = ((int) Math.ceil(PDWEIGHT * computeProportionalTerminationFactor() + (1 - PDWEIGHT) * computeDerivativeTerminationFactor())) - BASE_CAPACITY - computeExtraCapacity();
		System.out.println("computeServersToTerminate: " + i);
		return i;
	}

	private static double computeProportionalTerminationFactor() {
		double d = permanentlyIdleServers.size() * AGGRESSIVENESS_TERMINATION;
		System.out.println("computeProportionalTerminationFactor: " + d);
		return d;
	}

	private static double computeDerivativeTerminationFactor() {
		double d = currentPermanentlyIdleCount - lastPermanentlyIdleCount;
		System.out.println("computeDerivativeTerminationFactor: " + d);
		return d;
	}

	static class Provisioner implements Runnable {
		private static Provisioner instance;
		private static final int port = 8080;
		private static final Pattern requestPattern = Pattern.compile("^GET (http://\\S*)?/([^\\s\\?]*)(\\?\\S*)? HTTP/1\\.\\d$");
		private static final ServerSocket socket;
		private static final Random rand = new Random();
		private static volatile boolean done;

		private Provisioner() {
		}

		static Provisioner getInstance() {
			if (instance == null) {
				instance = new Provisioner();
			}

			return instance;
		}


		static {
			try {
				socket = new ServerSocket(port);
			} catch (IOException ex) {
				throw new RuntimeException(ex.getMessage(), ex);
			}
		}

		public void run() {
			while (!done) {
				try {
					Socket listen_socket = socket.accept();
					PrintStream outStream = new PrintStream(listen_socket.getOutputStream());
					BufferedReader reader = new BufferedReader(new InputStreamReader(listen_socket.getInputStream()));
					Matcher matcher = requestPattern.matcher(reader.readLine());
					StringBuilder responseStringBuilder = new StringBuilder("HTTP/1.1 ");
					if (matcher.matches()) {
						String applicationName = matcher.group(2);
						if (!applicationName.isEmpty()) {
							String version = null;
							Application application = new Application(applicationName, version);
							SetMultimap<Application, ApplicationServer> deployedApplications = applicationListener.getDeployedApplications();
							Set<ApplicationServer> servers = deployedApplications.get(application);
							synchronized (deployedApplications) {
								boolean deployOk = true;
								if (servers.isEmpty()) {
									deployOk = false;
									if (applicationRepository.hasApp(application)) {
										applicationListener.addPendingApplication(application);
										try {
											deploy(application, servers);
											deployOk = true;
										} catch (RemoteException ex) {
											Logger.getLogger(ArvueMaster.class.getName()).log(Level.SEVERE, null, ex);
										} catch (NotBoundException ex) {
											Logger.getLogger(ArvueMaster.class.getName()).log(Level.SEVERE, null, ex);
										} catch (DeploymentException ex) {
											Logger.getLogger(ArvueMaster.class.getName()).log(Level.SEVERE, null, ex);
										}
									} else {
										responseStringBuilder
											.append(404)
											.append(' ')
											.append("Not Found")
											.append(" - ")
											.append("Application ")
											.append(applicationName)
											.append(" was not found in application repository ")
											.append(applicationRepository.getName())
											.append("\r\n\r\n");
									}
								}
								if (deployOk) {
									responseStringBuilder
										.append(302)
										.append(' ')
										.append("Found")
										.append("\r\n")
										.append("Location: ")
										.append('/')
										.append(matcher.group(2))
										.append("\r\n")
										.append("Content-Type: text/html")
										.append("\r\n")
										.append("Content-Length: 0")
										.append("\r\n\r\n");
									loadBalancer.configure(servers, applicationListener.getPendingApplications());
									loadBalancer.restart();
								} else {
									responseStringBuilder
											.append(500)
											.append(' ')
											.append("Internal Server Error")
											.append(" - ")
											.append("The server encountered an unexpected condition which prevented it from fulfilling the request.")
											.append("\r\n\r\n");
								}
							}
						} else {
							responseStringBuilder
									.append(400)
									.append(' ')
									.append("Bad Request")
									.append(" - ")
									.append("No application specified")
									.append("\r\n\r\n");
						}
					} else {
						responseStringBuilder
								.append(405)
								.append(' ')
								.append("Method Not Allowed")
								.append(" - ")
								.append("This server only supports the GET method")
								.append("\r\n\r\n");
					}

					outStream.println(responseStringBuilder.toString());
					reader.close();
				} catch (IOException ex) {
					Logger.getLogger(Provisioner.class.getName()).log(Level.SEVERE, null, ex);
				}
			}
		}

		public void stop() {
			done = true;
		}

		private void deploy(Application application, Set<ApplicationServer> applicationServers) throws RemoteException, NotBoundException, DeploymentException {
			if (applicationServers == null) {
				throw new IllegalArgumentException("applicationServers cannot be null!");
			}

			if (applicationServers.isEmpty()) {
				int size = instanceManager.listInstances().size();
				PriorityQueue<ApplicationServer> pq = new PriorityQueue<ApplicationServer>(size, new Comparator<ApplicationServer>() {
					public int compare(ApplicationServer t, ApplicationServer t1) {
						try {
							if (t.status().getCpuLoad() < t1.status().getCpuLoad()) {
								return -1;
							} else if (t1.status().getCpuLoad() > t.status().getCpuLoad()) {
								return 1;
							} else {
								return 0;
							}
						} catch (RemoteException ex) {
							Logger.getLogger(ArvueMaster.class.getName()).log(Level.SEVERE, null, ex);
						} catch (PerformanceException ex) {
							Logger.getLogger(ArvueMaster.class.getName()).log(Level.SEVERE, null, ex);
						}
						return 0;
					}
				});

				for (String name : appServerRegistry.list()) {
					try {
						Remote remote = appServerRegistry.lookup(name);
						if (remote instanceof ApplicationServer) {
							ApplicationServer appServer = (ApplicationServer) remote;
							pq.add(appServer);
						}
					} catch (NotBoundException ex) {
						Logger.getLogger(ArvueMaster.class.getName()).log(Level.SEVERE, null, ex);
					}
				}

				pq.peek().deploy(application.getName(), application.getVersion());
			}
		}
	}
}
