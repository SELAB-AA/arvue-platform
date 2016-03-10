
/*
* To change this template, choose Tools | Templates
* and open the template in the editor.
 */
package org.vaadin.arvue.application.repository;

import com.amazonaws.AmazonServiceException;
import com.amazonaws.auth.AWSCredentials;
import com.amazonaws.auth.BasicAWSCredentials;
import com.amazonaws.services.s3.AmazonS3;
import com.amazonaws.services.s3.AmazonS3Client;
import com.amazonaws.services.s3.model.S3Object;
import java.io.FileOutputStream;
import org.vaadin.arvue.application.Application;
import java.io.IOException;
import org.apache.commons.io.IOUtils;

/**
 *
 * @author bbyholm
 */
public class S3ApplicationRepository implements ApplicationRepository {
	private static final long serialVersionUID = 8649134946130432784L;
    private static final RepositoryType type = RepositoryType.S3;

    private String name;
	private String bucket;
	private AmazonS3 s3;

	S3ApplicationRepository(String name) throws S3ApplicationRepositoryException {
		this(name, null, null);
	}

    S3ApplicationRepository(String name, String accessKey, String privateKey) throws S3ApplicationRepositoryException {
		if (name == null) {
                    throw new IllegalArgumentException("name cannot be null");
                }

		if (name.isEmpty()) {
			throw new IllegalArgumentException("name cannot be empty");
		}

		AWSCredentials credentials = new BasicAWSCredentials(accessKey, privateKey);

		s3 = new AmazonS3Client(credentials);

		if (!s3.doesBucketExist(name)) {
			throw new S3ApplicationRepositoryException("Bucket " + name + " does not exist.");
		}


		this.name = name;
		bucket = name;
    }

    @Override
    public boolean hasApp(Application app) {
		if (app == null) {
			throw new IllegalArgumentException("app");
		}

		try {
			s3.getObjectMetadata(bucket, app.getBundleName());
		} catch (AmazonServiceException ex) {
			if (ex.getStatusCode() == 404) {
				return false;
			} else {
				throw ex;
			}
		}

		return true;

    }

    @Override
    public String getName() {
        return name;
    }

    @Override
    public RepositoryType getType() {
        return type;
    }

	@Override
	public void get(Application app, String path) throws IOException {
		if (app == null) {
			throw new IllegalArgumentException("app");
		}

		if (path == null || path.isEmpty()) {
			throw new IllegalArgumentException("path");
		}

		if (!hasApp(app)) {
			throw new IOException("App " + app.getName() + " does not exist.");
		}


		StringBuilder sb = new StringBuilder(path);
		if (path.charAt(path.length() - 1) != IOUtils.DIR_SEPARATOR) {
			sb.append(IOUtils.DIR_SEPARATOR);
		}

		sb.append(app.getBundleName());

		FileOutputStream out = new FileOutputStream(sb.toString());

		try {
			S3Object o = s3.getObject(bucket, app.getBundleName());
			try {
				long copied;

				if (o.getObjectMetadata().getContentLength() <= Integer.MAX_VALUE) {
					copied = IOUtils.copy(o.getObjectContent(), out);
				} else {
					copied = IOUtils.copyLarge(o.getObjectContent(), out);
				}

				if (copied != o.getObjectMetadata().getContentLength()) {
					throw new IOException("Content length mismatch!");
				}
			} finally {
				o.getObjectContent().close();
			}
		} finally {
			out.close();
		}
	}
}