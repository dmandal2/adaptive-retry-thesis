package com.retrythesis.tests;

import org.testng.Assert;
import org.testng.annotations.Test;

public class FlakyTest {

	@Test(retryAnalyzer = RetryAnalyzer.class)
	public void testRandomFlaky() {
		double randomValue = Math.random(); // generates value between 0.0 and 1.0
		System.out.println("Generated value: " + randomValue);
		Assert.assertTrue(randomValue > 0.5, "Flaky test failed: value <= 0.5");
	}
}
