package org.vaadin.arvue.resourcecollector;

import java.io.IOException;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.logging.Level;
import java.util.logging.Logger;
import javax.servlet.ServletException;
import org.osgi.framework.BundleActivator;
import org.osgi.framework.BundleContext;
import org.osgi.framework.BundleEvent;
import org.osgi.framework.BundleListener;
import org.osgi.framework.ServiceReference;
import org.osgi.service.http.HttpService;
import org.osgi.service.http.NamespaceException;
import org.osgi.util.tracker.ServiceTracker;

public class Activator implements BundleActivator, BundleListener {
	private ServiceTracker tracker;

	@Override
    public void start(BundleContext context) throws Exception {
		System.out.println("Starting to listen for bundle events.");
		context.addBundleListener(this);

		tracker = new ServiceTracker(context, HttpService.class.getName(), null) {
			@Override
			public Object addingService(ServiceReference ref) {
				Object service =  super.addingService(ref);
				serviceAdded((HttpService)service);
				return service;
			}

			@Override
			public void removedService(ServiceReference ref, Object service) {
				serviceRemoved((HttpService)service);
				super.removedService(ref, service);
			}
		};

		tracker.open();
    }

	@Override
    public void stop(BundleContext context) throws Exception {
        context.removeBundleListener(this);
		System.out.println("Stopped listening for bundle events.");
		tracker.close();
    }

	@Override
	public void bundleChanged(BundleEvent be) {
		switch (be.getType()) {
			case BundleEvent.INSTALLED:
				System.out.println(be.getBundle().getSymbolicName() + " INSTALLED");
				break;
			case BundleEvent.LAZY_ACTIVATION:
				System.out.println(be.getBundle().getSymbolicName() + " LAZY_ACTIVATION");
				break;
			case BundleEvent.RESOLVED:
				System.out.println(be.getBundle().getSymbolicName() + " RESOLVED");
				try {
					URL url = new URL("http://localhost:8000/Applications/Deployed/" + be.getBundle().getSymbolicName().replaceFirst("com\\.arvue\\.", ""));
					HttpURLConnection connection = (HttpURLConnection) url.openConnection();
					connection.setRequestMethod("POST");
					System.out.println("Response: " + connection.getResponseCode());
				} catch (IOException ex) {
					Logger.getLogger(Activator.class.getName()).log(Level.SEVERE, null, ex);
				}
				break;
			case BundleEvent.STARTED:
				System.out.println(be.getBundle().getSymbolicName() + " STARTED");
				break;
			case BundleEvent.STARTING:
				System.out.println(be.getBundle().getSymbolicName() + " STARTING");
				break;
			case BundleEvent.STOPPED:
				System.out.println(be.getBundle().getSymbolicName() + " STOPPED");
				break;
			case BundleEvent.STOPPING:
				System.out.println(be.getBundle().getSymbolicName() + " STOPPING");
				break;
			case BundleEvent.UNINSTALLED:
				System.out.println(be.getBundle().getSymbolicName() + " UNINSTALLED");
				break;
			case BundleEvent.UNRESOLVED:
				System.out.println(be.getBundle().getSymbolicName() + " UNRESOLVED");
				try {
					URL url = new URL("http://localhost:8000/Applications/Deployed/" + be.getBundle().getSymbolicName().replaceFirst("com\\.arvue\\.", ""));
					HttpURLConnection connection = (HttpURLConnection) url.openConnection();
					connection.setRequestMethod("DELETE");
					System.out.println("Response: " + connection.getResponseCode());
				} catch (IOException ex) {
					Logger.getLogger(Activator.class.getName()).log(Level.SEVERE, null, ex);
				}
				break;
			case BundleEvent.UPDATED:
				System.out.println(be.getBundle().getSymbolicName() + " UPDATED");
				break;
			default:
				throw new RuntimeException("Unknown Bundle Event Type!");
		}
	}

	private void serviceAdded(HttpService service) {
		try {
			service.registerServlet("/ResourceManager", new ResourceManager(), null, null);
		} catch (ServletException ex) {
			Logger.getLogger(Activator.class.getName()).log(Level.SEVERE, null, ex);
		} catch (NamespaceException ex) {
			Logger.getLogger(Activator.class.getName()).log(Level.SEVERE, null, ex);
		}
	}

	private void serviceRemoved(HttpService service) {
		service.unregister("ResourceManager");
	}
}
