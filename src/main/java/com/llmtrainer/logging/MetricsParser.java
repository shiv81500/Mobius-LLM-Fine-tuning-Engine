package com.llmtrainer.logging;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Parses training metrics from Python training script log lines.
 */
public class MetricsParser {

    // Pattern to match: "Loss: 1.234"
    private static final Pattern LOSS_PATTERN = Pattern.compile("Loss:\\s*([0-9]*\\.?[0-9]+)");

    // Pattern to match: "Epoch 2/3" or "Epoch: 2/3"
    private static final Pattern EPOCH_PATTERN = Pattern.compile("Epoch:?\\s*(\\d+)/(\\d+)");

    // Pattern to match: "Step 350/500" or "Step: 350/500"
    private static final Pattern STEP_PATTERN = Pattern.compile("Step:?\\s*(\\d+)/(\\d+)");

    // Pattern to match: "Speed: 12.5 samples/sec"
    private static final Pattern SPEED_PATTERN = Pattern.compile("Speed:\\s*([0-9]*\\.?[0-9]+)\\s*samples/sec");

    // Pattern to match: "ETA: 01:25:30" or "Remaining: 01:25:30"
    private static final Pattern ETA_PATTERN = Pattern.compile("(?:ETA|Remaining):\\s*([0-9:]+)");

    /**
     * Parse a log line and update metrics if any are found.
     * @param logLine The log line to parse
     * @param metrics The metrics object to update
     */
    public static void parseLogLine(String logLine, TrainingMetrics metrics) {
        if (logLine == null || logLine.isEmpty()) {
            return;
        }

        // Try to extract loss
        Matcher lossMatcher = LOSS_PATTERN.matcher(logLine);
        if (lossMatcher.find()) {
            try {
                float loss = Float.parseFloat(lossMatcher.group(1));
                metrics.setLoss(loss);
            } catch (NumberFormatException e) {
                // Ignore parse errors
            }
        }

        // Try to extract epoch
        Matcher epochMatcher = EPOCH_PATTERN.matcher(logLine);
        if (epochMatcher.find()) {
            try {
                int currentEpoch = Integer.parseInt(epochMatcher.group(1));
                int totalEpochs = Integer.parseInt(epochMatcher.group(2));
                metrics.setCurrentEpoch(currentEpoch);
                metrics.setTotalEpochs(totalEpochs);
            } catch (NumberFormatException e) {
                // Ignore parse errors
            }
        }

        // Try to extract step
        Matcher stepMatcher = STEP_PATTERN.matcher(logLine);
        if (stepMatcher.find()) {
            try {
                int currentStep = Integer.parseInt(stepMatcher.group(1));
                int totalSteps = Integer.parseInt(stepMatcher.group(2));
                metrics.setCurrentStep(currentStep);
                metrics.setTotalSteps(totalSteps);
            } catch (NumberFormatException e) {
                // Ignore parse errors
            }
        }

        // Try to extract speed
        Matcher speedMatcher = SPEED_PATTERN.matcher(logLine);
        if (speedMatcher.find()) {
            try {
                float speed = Float.parseFloat(speedMatcher.group(1));
                metrics.setSamplesPerSecond(speed);
            } catch (NumberFormatException e) {
                // Ignore parse errors
            }
        }

        // Try to extract ETA
        Matcher etaMatcher = ETA_PATTERN.matcher(logLine);
        if (etaMatcher.find()) {
            metrics.setEstimatedTimeRemaining(etaMatcher.group(1));
        }
    }
}
