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
		if (retryCount < maxRetryCount) {
			logger.info("Retrying test '{}' | Attempt: {} | Time: {}", result.getName(), retryCount + 1,
					System.currentTimeMillis());
			retryCount++;
			return true;
		} else {
			logger.info("Test '{}' failed after {} attempts.", result.getName(), retryCount);
		}
		return false;
	}
}
