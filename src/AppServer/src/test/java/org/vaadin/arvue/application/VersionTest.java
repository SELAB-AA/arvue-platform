
/*
* To change this template, choose Tools | Templates
* and open the template in the editor.
 */
package org.vaadin.arvue.application;

//~--- non-JDK imports --------------------------------------------------------

import org.vaadin.arvue.application.Version;
import org.junit.Test;

import static org.junit.Assert.*;

/**
 *
 * @author User
 */
public class VersionTest {
    @Test(expected = IllegalArgumentException.class)
    public void nullConstructor() {
        Version v = new Version(null);
    }

    @Test(expected = IllegalArgumentException.class)
    public void emptyConstructor() {
        Version v = new Version("");
    }

    @Test
    public void simpleStringConstructor() {
        Version v = new Version("1");

        assertEquals(null, v.toString(), "1");
    }

    @Test
    public void stringConstructor() {
        Version v = new Version("1.3");

        assertEquals(null, v.toString(), "1.3");
    }

    @Test
    public void modifiedVersion() {
        Version v = new Version(1);

        v.setBuild(1337);
        assertEquals(null, v.toString(), "1.0.1337");
    }

    @Test
    public void ltComparison() {
        Version v1 = new Version(1, 3, 0, 2);
        Version v2 = new Version(1, 4);

        assertTrue(v1.compareTo(v2) < 0);
    }

    @Test
    public void gtComparison() {
        Version v1 = new Version(1, 3, 1);
        Version v2 = new Version(1, 3, 0, 99);

        assertTrue(v1.compareTo(v2) > 0);
    }

    @Test
    public void eqComparison() {
        Version v1 = new Version(1, 3, 1);
        Version v2 = new Version("1.3.1");

        assertTrue(v1.compareTo(v2) == 0);
    }
}


//~ Formatted by Jindent --- http://www.jindent.com
