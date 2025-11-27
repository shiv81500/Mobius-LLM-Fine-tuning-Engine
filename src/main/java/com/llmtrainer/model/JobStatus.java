package com.llmtrainer.model;

/**
 * Enum representing the possible states of a training job.
 */
public enum JobStatus {
    QUEUED,     // Waiting to start
    RUNNING,    // Currently executing Python training script
    PAUSED,     // User paused execution
    COMPLETED,  // Successfully finished
    FAILED,     // Encountered error
    CANCELLED   // User cancelled
}
