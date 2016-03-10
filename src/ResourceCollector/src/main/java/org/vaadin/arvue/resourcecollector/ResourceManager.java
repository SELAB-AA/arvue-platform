/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.resourcecollector;

import com.google.gson.Gson;
import fi.tut.cloud.arvue.resource.ResourceInfo;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.Map.Entry;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

/**
 *
 * @author bbyholm
 */
public class ResourceManager extends HttpServlet {
	private static final long serialVersionUID = 6912225077598102002L;
	private static Pattern threadGroupPattern = Pattern.compile("Vaadin Application ThreadGroup - /(\\S+)/.*");

	@Override
	protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
		ResourceInfo[] resources = ResourceInfo.getAll();
		Map<String, Long> usage = new HashMap<String, Long>();
		Map<String, Float> relativeUsage = new HashMap<String, Float>();

		for (ResourceInfo ri : resources) {
			Matcher m = threadGroupPattern.matcher(ri.sessionId);
			if (m.matches()) {

				String name = m.group(1);
				Long l = usage.get(name);
				if (l == null) {
					l = Long.valueOf(0);
				}
				l += ri.memUsage;
				usage.put(name, l);

			}
		}

		long runtimeMemory = Runtime.getRuntime().totalMemory();

		for (Entry<String, Long> e: usage.entrySet()) {
			relativeUsage.put(e.getKey(), new Float(((float) e.getValue()) / runtimeMemory));
		}

		resp.setContentType("application/json");
		resp.getWriter().write(new Gson().toJson(relativeUsage));
	}
}
