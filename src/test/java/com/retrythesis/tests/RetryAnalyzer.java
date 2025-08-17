package com.retrythesis.tests;

import java.io.File;
import org.testng.IRetryAnalyzer;
import org.testng.ITestResult;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class RetryAnalyzer implements IRetryAnalyzer {
	private int retryCount = 0;
	private static final int maxRetryCount = 2;

	// Create logs folder before logger is used
	static {
		File logDir = new File("logs");
		if (!logDir.exists()) {
			boolean created = logDir.mkdirs();
			if (created) {
				System.out.println("✅ Created 'logs' directory.");
			} else {
				System.out.println("❌ Failed to create 'logs' directory.");
			}
		} else {
			System.out.println("📁 'logs' directory already exists.");
		}
	}

	// Now init logger
	private static final Logger logger = LoggerFactory.getLogger(RetryAnalyzer.class);

	@Override
	public boolean retry(ITestResult result) {
		long duration = System.currentTimeMillis() - result.getStartMillis();

		if (retryCount < maxRetryCount) {
			logger.info("Retrying test '{}' | Status: {} | Attempt: {}/{} | Duration: {} ms", result.getName(),
					getStatusString(result.getStatus()), retryCount + 1, maxRetryCount, duration);
			retryCount++;
			return true;
		} else {
			logger.info("Test '{}' finished | Final Status: {} | Total Duration: {} ms (after {} attempts)",
					result.getName(), getStatusString(result.getStatus()), duration, retryCount);
			return false;
		}
	}

	private String getStatusString(int status) {
		switch (status) {
		case ITestResult.SUCCESS:
			return "PASS";
		case ITestResult.FAILURE:
			return "FAIL";
		case ITestResult.SKIP:
			return "SKIP";
		default:
			return "UNKNOWN";
		}
	}
}

