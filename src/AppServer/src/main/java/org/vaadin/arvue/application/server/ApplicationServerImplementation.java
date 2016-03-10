/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.application.server;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import com.sun.net.httpserver.HttpServer;
import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.InetSocketAddress;
import java.net.MalformedURLException;
import java.net.URL;
import java.net.URLConnection;
import java.rmi.AccessException;
import java.rmi.AlreadyBoundException;
import java.rmi.NotBoundException;
import java.rmi.RMISecurityManager;
import java.rmi.Remote;
import java.rmi.RemoteException;
import java.rmi.registry.LocateRegistry;
/* TODO: Use SSL
 * import java.rmi.server.RMIClientSocketFactory;
 * import java.rmi.server.RMIServerSocketFactory;
 */
import java.rmi.server.UnicastRemoteObject;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.Map.Entry;
import java.util.UUID;
import java.util.logging.Level;
import java.util.logging.Logger;
/* TODO: Use SSL
 * import javax.rmi.ssl.SslRMIClientSocketFactory;
 * import javax.rmi.ssl.SslRMIServerSocketFactory;
 */
import org.apache.commons.io.IOUtils;
import org.vaadin.arvue.application.Application;
import org.vaadin.arvue.application.ApplicationStatus;
import org.vaadin.arvue.application.listener.ApplicationListener;
import org.vaadin.arvue.application.repository.ApplicationRepository;
import org.vaadin.arvue.application.repository.ApplicationRepositoryException;
import org.vaadin.arvue.application.repository.ApplicationRepositoryFactory;
import org.vaadin.arvue.application.server.DeploymentException.Reason;
import org.vaadin.arvue.registry.ArvueRegistryInf;

/**
 *
 * @author User
 */
public class ApplicationServerImplementation implements ApplicationServer {
	private static ApplicationServerImplementation instance;
	private static String name;
    private static ApplicationRepository repository;
	private static ApplicationRepositoryFactory repositoryFactory;
    private static final Map<String, Application> deployedApps = Collections.synchronizedMap(new HashMap<String, Application>(256));
	private static String deployPath;
	private static ArvueRegistryInf registry;
	private static ApplicationListener applicationListener;
	private static int port = 9999;
	private static String publicAddress;
	private static String privateAddress;

	private static final String MASTER_ADDRESS = getMasterAddress();
    /**
     * @return the instance
     */
    static ApplicationServerImplementation getInstance() {
        if (instance == null) {
            instance = new ApplicationServerImplementation();
        }

        return instance;
    }

	/**
	 * @return the deployPath
	 */
	public final String getDeployPath() {
		return deployPath;
	}

	/**
	 * @param aDeployPath the deployPath to set
	 */
	public final void setDeployPath(String aDeployPath) {
		deployPath = aDeployPath;
	}

    private ApplicationServerImplementation() {
		if (System.getSecurityManager() == null) {
			System.setProperty("java.security.policy", getClass().getClassLoader().getResource("appserver.policy").toString());
			System.setSecurityManager(new RMISecurityManager());
		}

		boolean ec2 = false;
		BufferedReader reader = null;
		try {
			reader = new BufferedReader(new InputStreamReader(new URL("http://169.254.169.254/latest/meta-data/local-hostname").openStream()));
			privateAddress = reader.readLine();
			reader.close();
			reader = new BufferedReader(new InputStreamReader(new URL("http://169.254.169.254/latest/meta-data/public-hostname").openStream()));
			publicAddress = reader.readLine();
			reader.close();
			ec2 = true;
			Logger.getLogger(ApplicationServerImplementation.class.getName()).log(Level.INFO, "privateAddress : {0}", privateAddress);
			Logger.getLogger(ApplicationServerImplementation.class.getName()).log(Level.INFO, "publicAddress : {0}", publicAddress);
		} catch (IOException ex) {
			Logger.getLogger(ApplicationServerImplementation.class.getName()).log(Level.INFO, "Not running on ec2.");
		} finally {
			try {
				if (reader != null) {
					reader.close();
				}
			} catch (IOException ex) {
				Logger.getLogger(ApplicationServerImplementation.class.getName()).log(Level.SEVERE, null, ex);
			}
		}

		if (!ec2) {
			try {
				URLConnection urlc = new URL("http://automation.whatismyip.com/n09230945.asp").openConnection();
				urlc.setRequestProperty("User-Agent", "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.3) Gecko/2008092416 Firefox/3.0.3");
				reader = new BufferedReader(new InputStreamReader(urlc.getInputStream()));
				privateAddress = reader.readLine();
				reader.close();
				publicAddress = privateAddress;
				Logger.getLogger(ApplicationServerImplementation.class.getName()).log(Level.INFO, "privateAddress : {0}", privateAddress);
				Logger.getLogger(ApplicationServerImplementation.class.getName()).log(Level.INFO, "publicAddress : {0}", publicAddress);
			} catch (IOException ex) {
				Logger.getLogger(ApplicationServerImplementation.class.getName()).log(Level.SEVERE, "Error getting ip address.");
				throw new RuntimeException(ex.getMessage(), ex);
			} finally {
				try {
					if (reader != null) {
						reader.close();
					}
				} catch (IOException ex) {
					Logger.getLogger(ApplicationServerImplementation.class.getName()).log(Level.SEVERE, null, ex);
				}
			}
		}

		/*try {
			//create the service registry, or use one already available on this machine
			//in case master and appserver run on the same machine
			try {
				serviceRegistry = LocateRegistry.createRegistry(1099);
			} catch (ExportException ex) {
				serviceRegistry = LocateRegistry.getRegistry();
			}
		} catch (AccessException ex) {
			throw new RuntimeException(ex.getMessage(), ex);
		} catch (RemoteException ex) {
			throw new RuntimeException(ex.getMessage(), ex);
		}*/

        String defaultAppDir = new StringBuilder(11)
                .append("arvue")
                .append(IOUtils.DIR_SEPARATOR)
                .append("apps")
                .append(IOUtils.DIR_SEPARATOR)
                .toString();

		String appDir = System.getProperty("org.vaadin.arvue.appDir", defaultAppDir);

		File f = new File(System.getProperty("java.io.tmpdir"), appDir);
		deployPath = f.getAbsolutePath();
		System.setProperty("org.vaadin.arvue.appDir", deployPath);

		if (!f.exists()) {
			if (!f.mkdirs()) {
				throw new RuntimeException("Could not create deployment directory " + getDeployPath());
			}
		}

		if (!f.canWrite()) {
			throw new RuntimeException("Can not write to deployment directory " + getDeployPath());
		}
    }
    /**
     * @param args the command line arguments
     */
    public static void main(String[] args) {
		//boolean good = false;
		//while(!good) {
			try {
				name = getGeneratedName();
				/* TODO: Use SSL
				 * RMIClientSocketFactory csf = new SslRMIClientSocketFactory();
				 * RMIServerSocketFactory ssf = new SslRMIServerSocketFactory();
				 * ApplicationServer stub = (ApplicationServer) UnicastRemoteObject.exportObject(getInstance(), 0, csf, ssf);
				 */
				ApplicationServer stub = (ApplicationServer) UnicastRemoteObject.exportObject(getInstance(), 0);

				Remote remote = LocateRegistry.getRegistry(MASTER_ADDRESS).lookup("AppServerRegistry");
				if (remote instanceof ArvueRegistryInf) {
					registry = (ArvueRegistryInf) remote;
				} else {
					throw new RuntimeException("AppServerRegistry is no Registry");
				}

				System.out.println("AppServerRegistry gotten.");

				remote = LocateRegistry.getRegistry(MASTER_ADDRESS).lookup("ApplicationListener");

				if (remote instanceof ApplicationListener) {
					applicationListener = (ApplicationListener) remote;
				} else {
					throw new RuntimeException("ApplicationListener is no ApplicationListener");
				}

				try {
					HttpServer server = HttpServer.create(new InetSocketAddress(8000), 0);
					server.createContext("/", new ApplicationService(deployedApps, applicationListener));
					server.setExecutor(null);
					server.start();
				} catch (IOException ex) {
					Logger.getLogger(ApplicationServerImplementation.class.getName()).log(Level.SEVERE, null, ex);
				}

				System.out.println("Trying bind");

				registry.bind(name, stub);

				System.out.println("Bound");

				//good = true;
			} catch (AlreadyBoundException ex) {
				Logger.getLogger(ApplicationServerImplementation.class.getName()).log(Level.SEVERE, null, ex);
			} catch (NotBoundException ex) {
				Logger.getLogger(ApplicationServerImplementation.class.getName()).log(Level.SEVERE, null, ex);
			} catch (AccessException ex) {
				Logger.getLogger(ApplicationServerImplementation.class.getName()).log(Level.SEVERE, null, ex);
			} catch (RemoteException ex) {
				Logger.getLogger(ApplicationServerImplementation.class.getName()).log(Level.SEVERE, null, ex);
			}
		//}
    }

    @Override
    public void deploy(String appName) throws RemoteException, DeploymentException {
        deploy(appName, null);
    }

    @Override
    public void deploy(String appName, String version) throws RemoteException, DeploymentException {
		Application app = new Application(appName, version);
		synchronized (deployedApps) {
			if (!deployedApps.containsKey(appName)) {
				if (repository != null) {
					if (repository.hasApp(app)) {
						Logger.getLogger(ApplicationServerImplementation.class.getName()).log(Level.INFO, "App {0} exists.", appName);
						Logger.getLogger(ApplicationServerImplementation.class.getName()).log(Level.INFO, "Deploying {0} to Felix.", appName);
						try {
							deployedApps.put(appName, app);
							repository.get(app, getDeployPath());
						} catch (IOException ex) {
							deployedApps.remove(appName);
							throw new DeploymentException(Reason.CONNECTION);
						}

					} else {
						throw new DeploymentException(Reason.NONEXISTANT, appName);
					}
				} else {
					throw new DeploymentException(Reason.NOREPO);
				}
			} else {
				synchronized (app) {
					if (app.isAvailable()) {
						throw new DeploymentException(Reason.ALREADY_DEPLOYED, appName);
					} else {
						Logger.getLogger(ApplicationServerImplementation.class.getName()).log(Level.INFO, "Waiting for bundle...");
					}
				}
			}
		}
    }

    @Override
    public void undeploy(String appName) throws RemoteException, DeploymentException {
        undeploy(appName, null);
    }

    @Override
    public void undeploy(String appName, String version) throws RemoteException, DeploymentException {
		synchronized (deployedApps) {
			Application app = deployedApps.get(appName);
			if (app == null) {
				throw new DeploymentException(Reason.NOT_DEPLOYED, appName);
			}

			if (repository == null) {
				throw new DeploymentException(Reason.NOREPO);
			}

			StringBuilder sb = new StringBuilder(getDeployPath());
			if (getDeployPath().charAt(getDeployPath().length() - 1) != IOUtils.DIR_SEPARATOR) {
				sb.append(IOUtils.DIR_SEPARATOR);
			}

			sb.append(app.getBundleName());


			File f = new File(sb.toString());
			if (!f.exists()) {
				throw new DeploymentException(Reason.IO, sb.toString());
			}

			if (!f.canWrite()) {
				throw new DeploymentException(Reason.IO, sb.toString());
			}

			if (!f.delete()) {
				throw new DeploymentException(Reason.IO, sb.toString());
			}
			//deployedApps.remove(appName);
		}
    }

    @Override
    public ServerStatus status() throws RemoteException, PerformanceException {
		HashMap<String, Float> responseTimes;
		synchronized (deployedApps) {
			responseTimes = new HashMap<String, Float>(deployedApps.size());
			for (Application app : deployedApps.values()) {
				responseTimes.put(app.getName(), new Float(app.getAverageResponseTime()));
			}
		}
        return new ServerStatus(getName(), Performance.getCpuLoad(), Performance.getMemLoad(), responseTimes);
    }

    @Override
    public void setRepositoryFactory(ApplicationRepositoryFactory repositoryFactory) throws RemoteException, ApplicationRepositoryException {
        ApplicationServerImplementation.repositoryFactory = repositoryFactory;
		ApplicationServerImplementation.repository =  ApplicationServerImplementation.repositoryFactory.getRepository();
    }

    @Override
    public String[] getDeployedApps() throws RemoteException {
			ArrayList<String> names = new ArrayList<String>();

			synchronized (deployedApps) {
				for (Application application : deployedApps.values()) {
					synchronized (application) {
						if (application.isAvailable()) {
							String appName = application.getName();
							if (appName == null) {
								Logger.getLogger(ApplicationServerImplementation.class.getName()).log(Level.WARNING, "an application name was null");
							} else {
								names.add(appName);
							}
						}
					}
				}

				return names.toArray(new String[deployedApps.size()]);
			}
    }

	public String getName() throws RemoteException {
		return name;
	}

	private static String getGeneratedName() {
		return UUID.randomUUID().toString();
	}

	private static String getMasterAddress() {
		BufferedReader reader = null;

		try {
			reader = new BufferedReader(new InputStreamReader(new URL("http://169.254.169.254/latest/user-data").openStream()));
			String address = reader.readLine();
			reader.close();
			Logger.getLogger(ApplicationServerImplementation.class.getName()).log(Level.INFO, "masterAddress : {0}", address);
			return address;
		} catch (IOException ex) {
			Logger.getLogger(ApplicationServerImplementation.class.getName()).log(Level.INFO, "Not running on ec2.");
			return System.getProperty("master.address", "localhost");
		} finally {
			try {
				if (reader != null) {
					reader.close();
				}
			} catch (IOException ex) {
				Logger.getLogger(ApplicationServerImplementation.class.getName()).log(Level.SEVERE, null, ex);
			}
		}
	}

	public int getPort() throws RemoteException {
		return port;
	}

	public String getPublicAddress() throws RemoteException {
		return publicAddress;
	}

	public String getPrivateAddress() throws RemoteException {
		return privateAddress;
	}

	public void addResponseTime(String applicationName, int responseTime) throws RemoteException, DeploymentException {
		if (applicationName == null) {
			throw new IllegalArgumentException("applicationName cannot be null");
		}

		synchronized (deployedApps) {
			Application application = deployedApps.get(applicationName);
			if (application != null) {
				synchronized (application) {
					if (application.isAvailable()) {
						application.addResponseTime(responseTime);
					}
				}
			} else {
				throw new DeploymentException(Reason.NOT_DEPLOYED, "Application " + applicationName + " is not deployed.");
			}
		}
	}

	public String getInstanceID() throws RemoteException {
		String result = null;
		BufferedReader reader = null;
		try {
			reader = new BufferedReader(new InputStreamReader(new URL("http://169.254.169.254/latest/meta-data/instance-id").openStream()));
			result = reader.readLine();
		} catch (IOException ex) {
			Logger.getLogger(ApplicationServerImplementation.class.getName()).log(Level.SEVERE, null, ex);
		} finally {
			try {
				if (reader != null) {
					reader.close();
				}
			} catch (IOException ex) {
				Logger.getLogger(ApplicationServerImplementation.class.getName()).log(Level.SEVERE, null, ex);
			}
		}
		return result;
	}

	public ApplicationStatus[] applicationStatus() throws RemoteException {
		Gson g = new Gson();
		ApplicationStatus[] as = null;
		try {
			Map<String, Float> usage = g.fromJson(new BufferedReader(new InputStreamReader(new URL("http://localhost:9999/ResourceManager").openStream())), new TypeToken<Map<String, Float>>() {}.getType());
			as = new ApplicationStatus[usage.size()];

			int i = 0;

			for (Entry<String, Float> e : usage.entrySet()) {
				if (e.getValue() == null) {
					as[i] = new ApplicationStatus(e.getKey(), 0.0f);
				} else {
					as[i] = new ApplicationStatus(e.getKey(), e.getValue().floatValue());
				}
				i++;
			}
		} catch (MalformedURLException ex) {
			Logger.getLogger(ApplicationServerImplementation.class.getName()).log(Level.SEVERE, null, ex);
		} catch (IOException ex) {
			Logger.getLogger(ApplicationServerImplementation.class.getName()).log(Level.SEVERE, null, ex);
		}

		return as;
	}
}
