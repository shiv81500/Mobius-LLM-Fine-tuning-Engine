package com.llmtrainer;

import com.llmtrainer.api.ApiServer;
import com.llmtrainer.logging.LogStore;
import com.llmtrainer.model.JobStatus;
import com.llmtrainer.model.TrainingJob;
import com.llmtrainer.orchestrator.ProcessOrchestrator;
import com.llmtrainer.queue.JobQueueManager;
import com.llmtrainer.storage.DataManager;

import java.io.File;
import java.time.LocalDateTime;

/**
 * Main entry point for the LLM Training Backend.
 * Initializes all components and starts the API server.
 */
public class Main {
    private static final int API_PORT = 8080;
    private static final String DATA_DIR = "data";

    private static volatile boolean running = true;
    private static ApiServer apiServer;
    private static ProcessOrchestrator orchestrator;
    private static JobQueueManager queueManager;

    public static void main(String[] args) {
        System.out.println("===================================");
        System.out.println("LLM Training Backend");
        System.out.println("===================================");

        try {
            // Step 1: Create data directories
            System.out.println("Creating data directories...");
            createDataDirectories();

            // Step 2: Initialize components
            System.out.println("Initializing components...");

            // Initialize DataManager
            DataManager dataManager = new DataManager(DATA_DIR);
            System.out.println("Data Manager initialized");

            // Initialize JobQueueManager
            queueManager = new JobQueueManager();
            System.out.println("Job Queue Manager initialized");

            // Initialize LogStore
            LogStore logStore = new LogStore();
            System.out.println("Log Store initialized");

            // Initialize ProcessOrchestrator
            orchestrator = new ProcessOrchestrator(logStore);
            System.out.println("Process Orchestrator initialized");

            // Step 3: Start API server
            System.out.println("Starting HTTP server on port " + API_PORT + "...");
            apiServer = new ApiServer(API_PORT, queueManager, dataManager, logStore, orchestrator);
            apiServer.start();

            // Step 4: Start queue processor thread
            System.out.println("Starting job queue processor...");
            Thread queueProcessor = new Thread(new QueueProcessor(queueManager, orchestrator, logStore));
            queueProcessor.setDaemon(false);
            queueProcessor.start();

            // Step 5: Register shutdown hook
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                System.out.println("\nShutting down...");
                running = false;

                // Stop API server
                if (apiServer != null) {
                    apiServer.stop();
                }

                // Kill any running processes
                TrainingJob currentJob = queueManager.getCurrentRunningJob();
                if (currentJob != null) {
                    System.out.println("Stopping running job: " + currentJob.getJobId());
                    orchestrator.killProcess(currentJob.getJobId());
                }

                System.out.println("Shutdown complete");
            }));

            System.out.println("===================================");
            System.out.println("Backend ready. Press Ctrl+C to stop.");
            System.out.println("===================================");

            // Keep main thread alive
            while (running) {
                Thread.sleep(1000);
            }

        } catch (Exception e) {
            System.err.println("Fatal error: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }

    /**
     * Create necessary data directories.
     */
    private static void createDataDirectories() {
        String[] dirs = {
            DATA_DIR,
            DATA_DIR + "/datasets",
            DATA_DIR + "/models",
            DATA_DIR + "/gguf",
            DATA_DIR + "/logs"
        };

        for (String dir : dirs) {
            File directory = new File(dir);
            if (!directory.exists()) {
                directory.mkdirs();
            }
        }
    }

    /**
     * Queue processor thread - continuously processes queued jobs.
     */
    static class QueueProcessor implements Runnable {
        private final JobQueueManager queueManager;
        private final ProcessOrchestrator orchestrator;
        private final LogStore logStore;

        public QueueProcessor(JobQueueManager queueManager, ProcessOrchestrator orchestrator, LogStore logStore) {
            this.queueManager = queueManager;
            this.orchestrator = orchestrator;
            this.logStore = logStore;
        }

        @Override
        public void run() {
            System.out.println("Queue processor started");

            while (running) {
                try {
                    // Check current running job
                    TrainingJob currentJob = queueManager.getCurrentRunningJob();

                    if (currentJob != null) {
                        final String jobId = currentJob.getJobId();

                        // Check if process has terminated
                        Integer exitCode = orchestrator.getExitCode(jobId);
                        if (exitCode != null) {
                            // Process finished
                            if (exitCode == 0) {
                                currentJob.setStatus(JobStatus.COMPLETED);
                                currentJob.setCompletedAt(LocalDateTime.now());
                                System.out.println("Job completed: " + jobId);
                            } else {
                                currentJob.setStatus(JobStatus.FAILED);
                                currentJob.setCompletedAt(LocalDateTime.now());
                                System.out.println("Job failed: " + jobId + " (exit code: " + exitCode + ")");
                            }

                            // Clear current running job
                            queueManager.setCurrentRunningJob(null);
                        } else {
                            // Fallback: detect completion via log sentinel to avoid UI lag
                            try {
                                // Only attempt if not already marked completed/failed
                                if (currentJob.getStatus() == JobStatus.RUNNING) {
                                    var recent = logStore.getRecentLogs(jobId, 50);
                                    boolean hasCompleteMarker = false;
                                    for (String line : recent) {
                                        if (line == null) continue;
                                        // Sentinels emitted by training_script.py
                                        if (line.contains("=== Training job complete ===") ||
                                            line.contains("Merged model saved to ")) {
                                            hasCompleteMarker = true;
                                            break;
                                        }
                                    }
                                    if (hasCompleteMarker) {
                                        currentJob.setStatus(JobStatus.COMPLETED);
                                        currentJob.setCompletedAt(LocalDateTime.now());
                                        System.out.println("Job completed (by sentinel): " + jobId);
                                        // Free the slot so user can export immediately
                                        queueManager.setCurrentRunningJob(null);
                                    }
                                }
                            } catch (Exception ignored) {
                                // Non-fatal: continue polling normally
                            }
                        }
                    }

                    // Start next queued job if no job is running
                    if (queueManager.getCurrentRunningJob() == null && queueManager.hasQueuedJobs()) {
                        TrainingJob nextJob = queueManager.dequeueJob();
                        if (nextJob != null) {
                            System.out.println("Starting job: " + nextJob.getJobId());
                            try {
                                nextJob.setStatus(JobStatus.RUNNING);
                                queueManager.setCurrentRunningJob(nextJob);
                                orchestrator.startTraining(nextJob);
                            } catch (Exception e) {
                                System.err.println("Failed to start job " + nextJob.getJobId() + ": " + e.getMessage());
                                nextJob.setStatus(JobStatus.FAILED);
                                queueManager.setCurrentRunningJob(null);
                            }
                        }
                    }

                    // Sleep for 5 seconds before next check
                    Thread.sleep(5000);

                } catch (InterruptedException e) {
                    System.out.println("Queue processor interrupted");
                    break;
                } catch (Exception e) {
                    System.err.println("Error in queue processor: " + e.getMessage());
                    e.printStackTrace();
                }
            }

            System.out.println("Queue processor stopped");
        }
    }
}
