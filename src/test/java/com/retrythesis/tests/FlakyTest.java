package com.retrythesis.tests;

import org.testng.Assert;
import org.testng.annotations.Test;
import org.apache.log4j.Logger;  // Import log4j

public class FlakyTest {

    // Create a logger instance
    static Logger logger = Logger.getLogger(FlakyTest.class);

    @Test(retryAnalyzer = RetryAnalyzer.class)
    public void testRandomFlaky() {
        double randomValue = Math.random(); // generates value between 0.0 and 1.0

        // Log instead of just printing
        logger.info("Generated value: " + randomValue);

        Assert.assertTrue(randomValue > 0.5, "Flaky test failed: value <= 0.5");
    }
}
