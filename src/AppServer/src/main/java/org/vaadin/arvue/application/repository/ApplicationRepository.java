
/*
* To change this template, choose Tools | Templates
* and open the template in the editor.
 */
package org.vaadin.arvue.application.repository;

import java.io.IOException;
import org.vaadin.arvue.application.Application;

/**
 *
 * @author bbyholm
 */
public interface ApplicationRepository {
    public static enum RepositoryType { S3 };
    public boolean hasApp(Application app);

    public String getName();

    public RepositoryType getType();
	public void get(Application app, String path) throws IOException;
}