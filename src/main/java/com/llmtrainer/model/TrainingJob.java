package com.llmtrainer.model;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

/**
 * Represents a training job with all its configuration and state.
 */
public class TrainingJob {
    private String jobId;
    private String projectName;
    private JobStatus status;
    private String datasetPath;
    private String baseModel;
    private Map<String, Object> hyperparameters;
    private LocalDateTime createdAt;
    private LocalDateTime startedAt;
    private LocalDateTime completedAt;
    private String outputModelPath;
    private String ggufPath;
    private Long pythonProcessId;
    private String logFilePath;

    public TrainingJob(String jobId, String projectName, String datasetPath,
                      String baseModel, Map<String, Object> hyperparameters) {
        this.jobId = jobId;
        this.projectName = projectName;
        this.status = JobStatus.QUEUED;
        this.datasetPath = datasetPath;
        this.baseModel = baseModel;
        this.hyperparameters = new HashMap<>(hyperparameters);
        this.createdAt = LocalDateTime.now();
        this.startedAt = null;
        this.completedAt = null;
        this.outputModelPath = null;
        this.ggufPath = null;
        this.pythonProcessId = null;
        this.logFilePath = "data/logs/" + jobId + ".log";
    }

    // Getters and setters
    public String getJobId() {
        return jobId;
    }

    public void setJobId(String jobId) {
        this.jobId = jobId;
    }

    public String getProjectName() {
        return projectName;
    }

    public void setProjectName(String projectName) {
        this.projectName = projectName;
    }

    public JobStatus getStatus() {
        return status;
    }

    public void setStatus(JobStatus status) {
        this.status = status;
    }

    public String getDatasetPath() {
        return datasetPath;
    }

    public void setDatasetPath(String datasetPath) {
        this.datasetPath = datasetPath;
    }

    public String getBaseModel() {
        return baseModel;
    }

    public void setBaseModel(String baseModel) {
        this.baseModel = baseModel;
    }

    public Map<String, Object> getHyperparameters() {
        return hyperparameters;
    }

    public void setHyperparameters(Map<String, Object> hyperparameters) {
        this.hyperparameters = hyperparameters;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public LocalDateTime getStartedAt() {
        return startedAt;
    }

    public void setStartedAt(LocalDateTime startedAt) {
        this.startedAt = startedAt;
    }

    public LocalDateTime getCompletedAt() {
        return completedAt;
    }

    public void setCompletedAt(LocalDateTime completedAt) {
        this.completedAt = completedAt;
    }

    public String getOutputModelPath() {
        return outputModelPath;
    }

    public void setOutputModelPath(String outputModelPath) {
        this.outputModelPath = outputModelPath;
    }

    public String getGgufPath() {
        return ggufPath;
    }

    public void setGgufPath(String ggufPath) {
        this.ggufPath = ggufPath;
    }

    public Long getPythonProcessId() {
        return pythonProcessId;
    }

    public void setPythonProcessId(Long pythonProcessId) {
        this.pythonProcessId = pythonProcessId;
    }

    public String getLogFilePath() {
        return logFilePath;
    }

    public void setLogFilePath(String logFilePath) {
        this.logFilePath = logFilePath;
    }
}
