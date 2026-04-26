package com.devopsdays.qoe.framework.reporting;

import com.devopsdays.qoe.framework.models.ValidationResult;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.FileWriter;
import java.io.IOException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

public class TestReporter {
    private static final Logger logger = LoggerFactory.getLogger(TestReporter.class);
    
    public void generateReport(ValidationResult result, String outputPath) {
        try (FileWriter writer = new FileWriter(outputPath)) {
            writer.write("QoE Validation Report\n");
            writer.write("====================\n\n");
            writer.write("Generated: " + LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME) + "\n\n");
            writer.write("Validation Status: " + (result.isPassed() ? "PASSED" : "FAILED") + "\n");
            writer.write("Quality Score: " + String.format("%.2f", result.getQualityScore()) + "\n");
            
            if (result.getFailureReason() != null) {
                writer.write("Failure Reason: " + result.getFailureReason() + "\n");
            }
            
            logger.info("Report generated: {}", outputPath);
        } catch (IOException e) {
            logger.error("Failed to generate report", e);
        }
    }
}
