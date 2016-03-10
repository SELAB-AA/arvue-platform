package org.vaadin.arvue.loadbalancer.listener;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * This class represents the data logged by haproxy in http mode
 * @author bbyholm
 */
public class HTTPLogInfo {
	private static final Pattern haproxyPattern = Pattern.compile(
		"^(\\S+)\\[(\\d+)\\]:\\s" +								//process_name '[' pid ']:'
		"(\\S+):(\\d+)\\s" +									//client_ip ':' client_port
		"\\[(\\S+)\\]\\s" +										//'[' accept_date ']'
		"(\\S+)\\s" +											//frontend_name
		"(\\S+)/(\\S+)\\s" +									//backend_name '/' server_name
		"(-?\\d+)/(-?\\d+)/(-?\\d+)/(-?\\d+)/\\+?(\\d+)\\s" +	//Tq '/' Tw '/' Tc '/' Tr '/' Tt*
		"(\\d+)\\s" +											//status_code
		"\\+?(\\d*)\\s" +										//bytes_read*
		"(\\S+)\\s" +											//captured_request_cookie
		"(\\S+)\\s" +											//captured_response_cookie
		"(\\S+)\\s" +											//termination_state
		"(\\d+)/(\\d+)/(\\d+)/(\\d+)/\\+?(\\d+)\\s" +			//actconn '/' feconn '/' beconn '/' srv_conn '/' retries*
		"(\\d+)/(\\d+)\\s" +									//srv_queue '/' backend_queue
		"(\\{(.*)\\}\\s+)?" +									//'{' captured_request_headers* '}'
		"(\\{(.*)\\}\\s+)?" +									//'{' captured_response_headers* '}'
		"\"(.*)\"\\s*$"											//'"' http_request '"'
	);

	private final String   process_name;
	private final int      pid;
	private final String   client_ip;
	private final int      client_port;
	private final Date     accept_date;
	private final String   frontend_name;
	private final String   backend_name;
	private final String   server_name;
	private final int      tq;
	private final int      tw;
	private final int      tc;
	private final int      tr;
	private final int      tt;
	private final int      status_code;
	private final long     bytes_read;
	private final String   captured_request_cookie;
	private final String   captured_response_cookie;
	private final String   termination_state;
	private final int      actconn;
	private final int      feconn;
	private final int      beconn;
	private final int      srv_conn;
	private final int      retries;
	private final int      srv_queue;
	private final int      backend_queue;
	private final String[] captured_request_headers;
	private final String[] captured_response_headers;
	private final String   http_request;

	public HTTPLogInfo(String log_entry) throws ParseException {
		Matcher m = haproxyPattern.matcher(log_entry);

		if (!m.matches()) {
			throw new ParseException(log_entry, 0);
		}

		process_name = m.group(1);
		pid = Integer.parseInt(m.group(2));
		client_ip = m.group(3);
		client_port = Integer.parseInt(m.group(4));

		try {
			accept_date = new SimpleDateFormat("dd/MMM/yyyy:HH:mm:ss.SSS").parse(m.group(5));
		} catch (ParseException ex) {
			throw new RuntimeException(ex.getMessage(), ex);
		}

		frontend_name = m.group(6);
		backend_name = m.group(7);
		server_name = m.group(8);
		tq = Integer.parseInt(m.group(9));
		tw = Integer.parseInt(m.group(10));
		tc = Integer.parseInt(m.group(11));
		tr = Integer.parseInt(m.group(12));
		tt = Integer.parseInt(m.group(13));
		status_code = Integer.parseInt(m.group(14));
		bytes_read = Long.parseLong(m.group(15));
		captured_request_cookie = m.group(16);
		captured_response_cookie = m.group(17);
		termination_state = m.group(18);
		actconn = Integer.parseInt(m.group(19));
		feconn = Integer.parseInt(m.group(20));
		beconn = Integer.parseInt(m.group(21));
		srv_conn = Integer.parseInt(m.group(22));
		retries = Integer.parseInt(m.group(23));
		srv_queue = Integer.parseInt(m.group(24));
		backend_queue = Integer.parseInt(m.group(25));

		if (m.group(27) != null) {
			captured_request_headers = m.group(27).split("\\|");
		} else {
			captured_request_headers = null;
		}

		if (m.group(29) != null) {
			captured_response_headers = m.group(29).split("\\|");
		} else {
			captured_response_headers = null;
		}

		http_request = m.group(30);

	}

	/**
	 * @return the process_name
	 */
	public String getProcess_name() {
		return process_name;
	}

	/**
	 * @return the pid
	 */
	public int getPid() {
		return pid;
	}

	/**
	 * @return the client_ip
	 */
	public String getClient_ip() {
		return client_ip;
	}

	/**
	 * @return the client_port
	 */
	public int getClient_port() {
		return client_port;
	}

	/**
	 * @return the accept_date
	 */
	public Date getAccept_date() {
		return accept_date;
	}

	/**
	 * @return the frontend_name
	 */
	public String getFrontend_name() {
		return frontend_name;
	}

	/**
	 * @return the backend_name
	 */
	public String getBackend_name() {
		return backend_name;
	}

	/**
	 * @return the server_name
	 */
	public String getServer_name() {
		return server_name;
	}

	/**
	 * @return the tq
	 */
	public int getTq() {
		return tq;
	}

	/**
	 * @return the tw
	 */
	public int getTw() {
		return tw;
	}

	/**
	 * @return the tc
	 */
	public int getTc() {
		return tc;
	}

	/**
	 * @return the tr
	 */
	public int getTr() {
		return tr;
	}

	/**
	 * @return the tt
	 */
	public int getTt() {
		return tt;
	}

	/**
	 * @return the status_code
	 */
	public int getStatus_code() {
		return status_code;
	}

	/**
	 * @return the bytes_read
	 */
	public long getBytes_read() {
		return bytes_read;
	}

	/**
	 * @return the captured_request_cookie
	 */
	public String getCaptured_request_cookie() {
		return captured_request_cookie;
	}

	/**
	 * @return the captured_response_cookie
	 */
	public String getCaptured_response_cookie() {
		return captured_response_cookie;
	}

	/**
	 * @return the termination_state
	 */
	public String getTermination_state() {
		return termination_state;
	}

	/**
	 * @return the actconn
	 */
	public int getActconn() {
		return actconn;
	}

	/**
	 * @return the feconn
	 */
	public int getFeconn() {
		return feconn;
	}

	/**
	 * @return the beconn
	 */
	public int getBeconn() {
		return beconn;
	}

	/**
	 * @return the srv_conn
	 */
	public int getSrv_conn() {
		return srv_conn;
	}

	/**
	 * @return the retries
	 */
	public int getRetries() {
		return retries;
	}

	/**
	 * @return the srv_queue
	 */
	public int getSrv_queue() {
		return srv_queue;
	}

	/**
	 * @return the backend_queue
	 */
	public int getBackend_queue() {
		return backend_queue;
	}

	/**
	 * @return the captured_request_headers
	 */
	public String[] getCaptured_request_headers() {
		return captured_request_headers;
	}

	/**
	 * @return the captured_response_headers
	 */
	public String[] getCaptured_response_headers() {
		return captured_response_headers;
	}

	/**
	 * @return the http_request
	 */
	public String getHttp_request() {
		return http_request;
	}
}
