package com.retrythesis.tests;

import org.testng.ITestResult;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.Test;
import org.apache.log4j.Logger;

public class FlakyTest {
    static Logger logger = Logger.getLogger(FlakyTest.class);

    @Test(retryAnalyzer = RetryAnalyzer.class)
    public void testRandomFlaky() {
        double value = Math.random();
        double threshold = 0.5;  // Adjusted for balanced PASS/FAIL outcomes
        logger.info("Generated value: " + value + " | Threshold: " + threshold);
        org.testng.Assert.assertTrue(value > threshold, "Value did not meet threshold");
    }

    @AfterMethod
    public void logTestResult(ITestResult result) {
        String status = result.isSuccess() ? "PASS" : "FAIL";
        logger.info("Final Result | Test: " + result.getName() + " | Status: " + status);
    }
}
