/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.entertainmentserver;

import com.sun.net.httpserver.Headers;
import com.sun.net.httpserver.HttpContext;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 *
 * @author bbyholm
 */
public class EntertainmentServer implements HttpHandler {
	private static Pattern requestPattern = Pattern.compile("^/(\\S*)$");

	public static void main(String[] args) {
		try {
			HttpServer server = HttpServer.create(new InetSocketAddress(6666), 0);
			HttpContext ctx = server.createContext("/", new EntertainmentServer());
			server.setExecutor(null);
			server.start();
		} catch (IOException ex) {
			Logger.getLogger(EntertainmentServer.class.getName()).log(Level.SEVERE, null, ex);
		}
	}

	public void handle(HttpExchange he) throws IOException {
		Matcher matcher = requestPattern.matcher(he.getRequestURI().getPath());
		if (matcher.matches()) {
			String name = matcher.group(1);
			StringBuilder sb = new StringBuilder()
				.append("<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.0 Strict//EN\" \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd\">\n")
				.append("<html xmlns=\"http://www.w3.org/1999/xhtml\" lang=\"en\" xml:lang=\"en\">\n")
				.append("\t<head>\n")
				.append("\t\t<title>Arvue</title>\n")
				.append("\t</head>\n")
				.append("\t<body>\n")
				.append("\t\t<h1>")
				.append("Deployed application ")
				.append(name)
				.append('.')
				.append("</h1>\n")
				.append("\t</body>\n")
				.append("</html>");
			String response = sb.toString();
			Headers headers = he.getResponseHeaders();
			headers.set("ContentType", "text/html");
			headers.set("Refresh", "1; url=" + he.getRequestURI().toString());
			he.sendResponseHeaders(200, response.length());
			OutputStream out = he.getResponseBody();
			out.write(response.getBytes());
			out.close();
		}

	}

}
