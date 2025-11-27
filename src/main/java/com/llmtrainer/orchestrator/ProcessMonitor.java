package com.llmtrainer.orchestrator;

import com.llmtrainer.logging.LogStore;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;

/**
 * Monitors a process's stdout/stderr and streams output to LogStore.
 */
public class ProcessMonitor implements Runnable {
    private final Process process;
    private final String jobId;
    private final LogStore logStore;
    private final boolean isErrorStream;

    public ProcessMonitor(Process process, String jobId, LogStore logStore, boolean isErrorStream) {
        this.process = process;
        this.jobId = jobId;
        this.logStore = logStore;
        this.isErrorStream = isErrorStream;
    }

    @Override
    public void run() {
        InputStream stream = isErrorStream ? process.getErrorStream() : process.getInputStream();

        try (BufferedReader reader = new BufferedReader(new InputStreamReader(stream))) {
            String line;
            while ((line = reader.readLine()) != null) {
                // Append to log store
                logStore.appendLogLine(jobId, line);
            }
        } catch (IOException e) {
            // Process terminated or stream closed
            if (!isErrorStream) {
                logStore.appendLogLine(jobId, "Process stream closed: " + e.getMessage());
            }
        }
    }
}
