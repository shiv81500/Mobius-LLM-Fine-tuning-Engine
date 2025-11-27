package com.llmtrainer.logging;

import java.util.*;
import java.util.concurrent.locks.ReentrantLock;

/**
 * Stores training logs and metrics using a circular buffer for efficient streaming.
 * Each job has its own log buffer and metrics.
 */
public class LogStore {
    private static final int BUFFER_SIZE = 10000; // Keep last 10,000 log lines per job

    private final Map<String, CircularBuffer> logBuffers;
    private final Map<String, TrainingMetrics> metricsMap;
    private final ReentrantLock lock;

    public LogStore() {
        this.logBuffers = new HashMap<>();
        this.metricsMap = new HashMap<>();
        this.lock = new ReentrantLock();
    }

    /**
     * Append a log line for a specific job.
     * O(1) operation due to circular buffer.
     */
    public void appendLogLine(String jobId, String logLine) {
        lock.lock();
        try {
            // Get or create buffer for this job
            CircularBuffer buffer = logBuffers.computeIfAbsent(jobId, k -> new CircularBuffer(BUFFER_SIZE));
            buffer.add(logLine);

            // Get or create metrics for this job
            TrainingMetrics metrics = metricsMap.computeIfAbsent(jobId, k -> new TrainingMetrics());

            // Parse log line for metrics
            MetricsParser.parseLogLine(logLine, metrics);
        } finally {
            lock.unlock();
        }
    }

    /**
     * Get recent log lines for a job.
     * O(k) where k = number of lines requested.
     */
    public List<String> getRecentLogs(String jobId, int lastN) {
        lock.lock();
        try {
            CircularBuffer buffer = logBuffers.get(jobId);
            if (buffer == null) {
                return new ArrayList<>();
            }
            return buffer.getLastN(lastN);
        } finally {
            lock.unlock();
        }
    }

    /**
     * Get all logs for a job.
     */
    public List<String> getAllLogs(String jobId) {
        lock.lock();
        try {
            CircularBuffer buffer = logBuffers.get(jobId);
            if (buffer == null) {
                return new ArrayList<>();
            }
            return buffer.getAll();
        } finally {
            lock.unlock();
        }
    }

    /**
     * Get current metrics for a job.
     * O(1) operation.
     */
    public TrainingMetrics getCurrentMetrics(String jobId) {
        lock.lock();
        try {
            return metricsMap.get(jobId);
        } finally {
            lock.unlock();
        }
    }

    /**
     * Clear logs and metrics for a job.
     */
    public void clearJob(String jobId) {
        lock.lock();
        try {
            logBuffers.remove(jobId);
            metricsMap.remove(jobId);
        } finally {
            lock.unlock();
        }
    }

    /**
     * Circular buffer implementation for efficient log storage.
     * Overwrites oldest entries when full.
     */
    private static class CircularBuffer {
        private final String[] buffer;
        private final int capacity;
        private int head; // Points to the oldest element
        private int tail; // Points to where next element will be added
        private int size; // Current number of elements

        public CircularBuffer(int capacity) {
            this.buffer = new String[capacity];
            this.capacity = capacity;
            this.head = 0;
            this.tail = 0;
            this.size = 0;
        }

        /**
         * Add a new log line to the buffer.
         * O(1) operation.
         */
        public void add(String logLine) {
            buffer[tail] = logLine;
            tail = (tail + 1) % capacity;

            if (size < capacity) {
                size++;
            } else {
                // Buffer is full, move head forward (overwrite oldest)
                head = (head + 1) % capacity;
            }
        }

        /**
         * Get the last N log lines.
         * O(k) where k = n.
         */
        public List<String> getLastN(int n) {
            List<String> result = new ArrayList<>();
            int count = Math.min(n, size);

            if (count == 0) {
                return result;
            }

            // Calculate starting position
            int start = (tail - count + capacity) % capacity;

            for (int i = 0; i < count; i++) {
                int index = (start + i) % capacity;
                result.add(buffer[index]);
            }

            return result;
        }

        /**
         * Get all log lines in the buffer.
         * O(size) operation.
         */
        public List<String> getAll() {
            List<String> result = new ArrayList<>();

            if (size == 0) {
                return result;
            }

            for (int i = 0; i < size; i++) {
                int index = (head + i) % capacity;
                result.add(buffer[index]);
            }

            return result;
        }
    }
}
