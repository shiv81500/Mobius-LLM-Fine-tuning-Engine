package com.llmtrainer.logging;

/**
 * Represents current training metrics for a job.
 */
public class TrainingMetrics {
    private Float loss;
    private Integer currentEpoch;
    private Integer totalEpochs;
    private Integer currentStep;
    private Integer totalSteps;
    private Float samplesPerSecond;
    private String estimatedTimeRemaining;

    public TrainingMetrics() {
        this.loss = null;
        this.currentEpoch = null;
        this.totalEpochs = null;
        this.currentStep = null;
        this.totalSteps = null;
        this.samplesPerSecond = null;
        this.estimatedTimeRemaining = null;
    }

    // Getters and setters
    public Float getLoss() {
        return loss;
    }

    public void setLoss(Float loss) {
        this.loss = loss;
    }

    public Integer getCurrentEpoch() {
        return currentEpoch;
    }

    public void setCurrentEpoch(Integer currentEpoch) {
        this.currentEpoch = currentEpoch;
    }

    public Integer getTotalEpochs() {
        return totalEpochs;
    }

    public void setTotalEpochs(Integer totalEpochs) {
        this.totalEpochs = totalEpochs;
    }

    public Integer getCurrentStep() {
        return currentStep;
    }

    public void setCurrentStep(Integer currentStep) {
        this.currentStep = currentStep;
    }

    public Integer getTotalSteps() {
        return totalSteps;
    }

    public void setTotalSteps(Integer totalSteps) {
        this.totalSteps = totalSteps;
    }

    public Float getSamplesPerSecond() {
        return samplesPerSecond;
    }

    public void setSamplesPerSecond(Float samplesPerSecond) {
        this.samplesPerSecond = samplesPerSecond;
    }

    public String getEstimatedTimeRemaining() {
        return estimatedTimeRemaining;
    }

    public void setEstimatedTimeRemaining(String estimatedTimeRemaining) {
        this.estimatedTimeRemaining = estimatedTimeRemaining;
    }
}
