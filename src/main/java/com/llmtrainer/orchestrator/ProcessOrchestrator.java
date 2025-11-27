package com.llmtrainer.orchestrator;

import com.llmtrainer.logging.LogStore;
import com.llmtrainer.model.TrainingJob;

import java.io.File;
import java.io.IOException;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Orchestrates Python training and conversion processes using ProcessBuilder.
 */
public class ProcessOrchestrator {
    private final LogStore logStore;
    private final Map<String, Process> activeProcesses; // jobId -> Process
    private final String pythonCommand;

    public ProcessOrchestrator(LogStore logStore) {
        this.logStore = logStore;
        this.activeProcesses = new ConcurrentHashMap<>();
        // Use environment variable TRAINER_PYTHON if set, otherwise fall back to "python"
        this.pythonCommand = System.getenv().getOrDefault("TRAINER_PYTHON", "python");
    }

    /**
     * Start a training job by launching the Python training script.
     */
    public void startTraining(TrainingJob job) throws IOException {
        String jobId = job.getJobId();

        // Build command arguments
        List<String> command = new ArrayList<>();
        command.add(pythonCommand);
        command.add("ml_core/training_script.py");
        command.add("--job-id");
        command.add(jobId);
        command.add("--dataset");
        command.add(job.getDatasetPath());
        command.add("--base-model");
        command.add(job.getBaseModel());
        command.add("--output-dir");
        command.add("data/models/" + jobId);

        // Add hyperparameters
        Map<String, Object> hyperparams = job.getHyperparameters();
        if (hyperparams.containsKey("learningRate")) {
            command.add("--learning-rate");
            command.add(String.valueOf(hyperparams.get("learningRate")));
        }

        // Helper to format integer-valued hyperparameters so they are passed as ints
        java.util.function.BiConsumer<String, String> addIntParam = (paramName, cliName) -> {
            if (hyperparams.containsKey(paramName)) {
                Object v = hyperparams.get(paramName);
                String out;
                if (v instanceof Number) {
                    // Use integer value to avoid passing floats like "1.0"
                    out = String.valueOf(((Number) v).intValue());
                } else {
                    out = String.valueOf(v);
                }
                command.add(cliName);
                command.add(out);
            }
        };

        addIntParam.accept("epochs", "--epochs");
        addIntParam.accept("batchSize", "--batch-size");
        addIntParam.accept("loraRank", "--lora-rank");
        addIntParam.accept("loraAlpha", "--lora-alpha");
        addIntParam.accept("gradAccum", "--grad-accum");
        addIntParam.accept("maxLength", "--max-length");

        // Boolean / flag hyperparameters
        if (Boolean.TRUE.equals(hyperparams.get("stream"))) {
            command.add("--stream");
        }

        // Create output directory
        new File("data/models/" + jobId).mkdirs();

        // Set job started timestamp
        job.setStartedAt(LocalDateTime.now());
        job.setOutputModelPath("data/models/" + jobId);

        // Launch process
        ProcessBuilder pb = new ProcessBuilder(command);
        pb.directory(new File(".")); // Set working directory to project root
        pb.redirectErrorStream(false); // Keep stderr separate

    logStore.appendLogLine(jobId, "Starting training job: " + jobId);
    logStore.appendLogLine(jobId, "Command: " + String.join(" ", command));

        Process process = pb.start();
        activeProcesses.put(jobId, process);

        // Store process ID (Java 9+)
        try {
            long pid = process.pid();
            job.setPythonProcessId(pid);
            logStore.appendLogLine(jobId, "Process started with PID: " + pid);
        } catch (UnsupportedOperationException e) {
            // Process.pid() not available in Java 8
            logStore.appendLogLine(jobId, "Process started (PID not available)");
        }

        // Start monitoring threads for stdout and stderr
        Thread stdoutMonitor = new Thread(new ProcessMonitor(process, jobId, logStore, false));
        Thread stderrMonitor = new Thread(new ProcessMonitor(process, jobId, logStore, true));
        stdoutMonitor.setDaemon(true);
        stderrMonitor.setDaemon(true);
        stdoutMonitor.start();
        stderrMonitor.start();
    }

    /**
     * Start GGUF conversion for a completed training job.
     */
    public void startConversion(TrainingJob job) throws IOException {
        String jobId = job.getJobId();
        String quantization = (String) job.getHyperparameters().getOrDefault("quantization", "Q4_K_M");

        // Build command arguments
        List<String> command = new ArrayList<>();
        command.add(pythonCommand);
        command.add("ml_core/convert_to_gguf.py");
        command.add("--model-dir");
        command.add(job.getOutputModelPath() + "/merged");
        command.add("--output-file");
        command.add("data/gguf/" + jobId + ".gguf");
        command.add("--quantization");
        command.add(quantization);

        // Create gguf directory
        new File("data/gguf").mkdirs();

        logStore.appendLogLine(jobId, "Starting GGUF conversion for job: " + jobId);
        logStore.appendLogLine(jobId, "Command: " + String.join(" ", command));

        // Launch process
        ProcessBuilder pb = new ProcessBuilder(command);
        pb.directory(new File(".")); // Set working directory to project root
        pb.redirectErrorStream(false);

        Process process = pb.start();

        // We don't track conversion processes in activeProcesses map
        // They run to completion independently

        // Monitor output in separate threads
        String conversionJobId = jobId + "-conversion";
        Thread stdoutMonitor = new Thread(new ProcessMonitor(process, conversionJobId, logStore, false));
        Thread stderrMonitor = new Thread(new ProcessMonitor(process, conversionJobId, logStore, true));
        stdoutMonitor.setDaemon(true);
        stderrMonitor.setDaemon(true);
        stdoutMonitor.start();
        stderrMonitor.start();

        // Wait for conversion to complete in a separate thread
        new Thread(() -> {
            try {
                int exitCode = process.waitFor();
                if (exitCode == 0) {
                    logStore.appendLogLine(conversionJobId, "GGUF conversion completed successfully");
                    job.setGgufPath("data/gguf/" + jobId + ".gguf");
                } else {
                    logStore.appendLogLine(conversionJobId, "GGUF conversion failed with exit code: " + exitCode);
                }
            } catch (InterruptedException e) {
                logStore.appendLogLine(conversionJobId, "GGUF conversion interrupted");
            }
        }).start();
    }

    /**
     * Pause a running process (SIGSTOP - Linux/Mac only).
     */
    public boolean pauseProcess(String jobId) {
        Process process = activeProcesses.get(jobId);
        if (process == null || !process.isAlive()) {
            return false;
        }

        try {
            long pid = process.pid();
            // Send SIGSTOP signal (Linux/Mac)
            Runtime.getRuntime().exec(new String[]{"kill", "-STOP", String.valueOf(pid)});
            logStore.appendLogLine(jobId, "Process paused (SIGSTOP sent to PID " + pid + ")");
            return true;
        } catch (Exception e) {
            logStore.appendLogLine(jobId, "Failed to pause process: " + e.getMessage());
            return false;
        }
    }

    /**
     * Resume a paused process (SIGCONT - Linux/Mac only).
     */
    public boolean resumeProcess(String jobId) {
        Process process = activeProcesses.get(jobId);
        if (process == null || !process.isAlive()) {
            return false;
        }

        try {
            long pid = process.pid();
            // Send SIGCONT signal (Linux/Mac)
            Runtime.getRuntime().exec(new String[]{"kill", "-CONT", String.valueOf(pid)});
            logStore.appendLogLine(jobId, "Process resumed (SIGCONT sent to PID " + pid + ")");
            return true;
        } catch (Exception e) {
            logStore.appendLogLine(jobId, "Failed to resume process: " + e.getMessage());
            return false;
        }
    }

    /**
     * Kill a running process (SIGKILL).
     */
    public boolean killProcess(String jobId) {
        Process process = activeProcesses.get(jobId);
        if (process == null) {
            return false;
        }

        try {
            process.destroyForcibly();
            activeProcesses.remove(jobId);
            logStore.appendLogLine(jobId, "Process terminated (SIGKILL sent)");
            return true;
        } catch (Exception e) {
            logStore.appendLogLine(jobId, "Failed to kill process: " + e.getMessage());
            return false;
        }
    }

    /**
     * Check if a process is still alive.
     */
    public boolean isProcessAlive(String jobId) {
        Process process = activeProcesses.get(jobId);
        return process != null && process.isAlive();
    }

    /**
     * Get exit code of a completed process.
     * Returns null if process is still running or doesn't exist.
     */
    public Integer getExitCode(String jobId) {
        Process process = activeProcesses.get(jobId);
        if (process == null) {
            return null;
        }

        if (process.isAlive()) {
            return null;
        }

        return process.exitValue();
    }

    /**
     * Wait for a process to complete and return exit code.
     */
    public int waitForCompletion(String jobId) throws InterruptedException {
        Process process = activeProcesses.get(jobId);
        if (process == null) {
            throw new IllegalStateException("No process found for job: " + jobId);
        }

        int exitCode = process.waitFor();
        activeProcesses.remove(jobId);
        return exitCode;
    }
}
