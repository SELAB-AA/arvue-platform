/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package org.vaadin.arvue.application.repository;


/**
 *
 * @author bbyholm
 */
public class S3ApplicationRepositoryException extends ApplicationRepositoryException {
	private static final long serialVersionUID = 7475211059217065579L;
	//private static final String newLine = System.getProperty("line.separator");
	//private final S3ServiceException ex;
	private String msg;

	/*S3ApplicationRepositoryException(S3ServiceException ex) {
		super(ex);
		this.ex = ex;
	}*/

	S3ApplicationRepositoryException(String msg) {
		super(msg);
		//ex = null;
		this.msg = msg == null ? "" : msg;
	}

	public String getS3Message() {
		//if (ex == null) {
			return msg;
		//}
		/*return new StringBuilder()
				.append(ex.getS3ErrorCode())
				.append(newLine)
				.append(ex.getS3ErrorHostId())
				.append(newLine)
				.append(ex.getS3ErrorMessage())
				.append(newLine)
				.append(ex.getS3ErrorRequestId())
				.toString();*/
	}
}