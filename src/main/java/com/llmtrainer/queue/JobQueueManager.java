package com.llmtrainer.queue;

import com.llmtrainer.model.JobStatus;
import com.llmtrainer.model.TrainingJob;

import java.util.*;
import java.util.concurrent.locks.ReentrantLock;

/**
 * Manages training jobs using a LinkedList-based FIFO queue.
 * Provides O(1) enqueue, dequeue, and peek operations.
 */
public class JobQueueManager {
    private final LinkedList<TrainingJob> queue;
    private final Map<String, TrainingJob> jobMap; // For O(1) lookup by jobId
    private TrainingJob currentRunningJob;
    private final ReentrantLock lock;

    public JobQueueManager() {
        this.queue = new LinkedList<>();
        this.jobMap = new HashMap<>();
        this.currentRunningJob = null;
        this.lock = new ReentrantLock();
    }

    /**
     * Add a new training job to the queue.
     * O(1) operation.
     */
    public void enqueueJob(TrainingJob job) {
        lock.lock();
        try {
            job.setStatus(JobStatus.QUEUED);
            queue.addLast(job);
            jobMap.put(job.getJobId(), job);
        } finally {
            lock.unlock();
        }
    }

    /**
     * Remove and return the next job from the queue.
     * O(1) operation.
     * Returns null if queue is empty.
     */
    public TrainingJob dequeueJob() {
        lock.lock();
        try {
            if (queue.isEmpty()) {
                return null;
            }
            TrainingJob job = queue.removeFirst();
            return job;
        } finally {
            lock.unlock();
        }
    }

    /**
     * View the next job without removing it.
     * O(1) operation.
     * Returns null if queue is empty.
     */
    public TrainingJob peekJob() {
        lock.lock();
        try {
            return queue.isEmpty() ? null : queue.getFirst();
        } finally {
            lock.unlock();
        }
    }

    /**
     * Get a job by its ID.
     * O(1) average case lookup.
     */
    public TrainingJob getJob(String jobId) {
        lock.lock();
        try {
            return jobMap.get(jobId);
        } finally {
            lock.unlock();
        }
    }

    /**
     * Cancel a job (remove from queue or mark as cancelled if running).
     */
    public boolean cancelJob(String jobId) {
        lock.lock();
        try {
            TrainingJob job = jobMap.get(jobId);
            if (job == null) {
                return false;
            }

            if (job.getStatus() == JobStatus.QUEUED) {
                // Remove from queue
                queue.remove(job);
                job.setStatus(JobStatus.CANCELLED);
                return true;
            } else if (job.getStatus() == JobStatus.RUNNING || job.getStatus() == JobStatus.PAUSED) {
                // Mark as cancelled (ProcessOrchestrator will handle process termination)
                job.setStatus(JobStatus.CANCELLED);
                if (currentRunningJob != null && currentRunningJob.getJobId().equals(jobId)) {
                    currentRunningJob = null;
                }
                return true;
            }
            return false;
        } finally {
            lock.unlock();
        }
    }

    /**
     * Pause a running job.
     */
    public boolean pauseJob(String jobId) {
        lock.lock();
        try {
            TrainingJob job = jobMap.get(jobId);
            if (job != null && job.getStatus() == JobStatus.RUNNING) {
                job.setStatus(JobStatus.PAUSED);
                return true;
            }
            return false;
        } finally {
            lock.unlock();
        }
    }

    /**
     * Resume a paused job.
     */
    public boolean resumeJob(String jobId) {
        lock.lock();
        try {
            TrainingJob job = jobMap.get(jobId);
            if (job != null && job.getStatus() == JobStatus.PAUSED) {
                job.setStatus(JobStatus.RUNNING);
                return true;
            }
            return false;
        } finally {
            lock.unlock();
        }
    }

    /**
     * Get the currently running job.
     */
    public TrainingJob getCurrentRunningJob() {
        lock.lock();
        try {
            return currentRunningJob;
        } finally {
            lock.unlock();
        }
    }

    /**
     * Set the currently running job.
     */
    public void setCurrentRunningJob(TrainingJob job) {
        lock.lock();
        try {
            this.currentRunningJob = job;
        } finally {
            lock.unlock();
        }
    }

    /**
     * Get list of all jobs (queued, running, completed, etc.).
     */
    public List<TrainingJob> getAllJobs() {
        lock.lock();
        try {
            return new ArrayList<>(jobMap.values());
        } finally {
            lock.unlock();
        }
    }

    /**
     * Get queue status (all jobs with their states).
     */
    public List<TrainingJob> getQueueStatus() {
        return getAllJobs();
    }

    /**
     * Check if there are any queued jobs waiting.
     */
    public boolean hasQueuedJobs() {
        lock.lock();
        try {
            return !queue.isEmpty();
        } finally {
            lock.unlock();
        }
    }

    /**
     * Get number of jobs in queue (QUEUED status only).
     */
    public int getQueueSize() {
        lock.lock();
        try {
            return queue.size();
        } finally {
            lock.unlock();
        }
    }
}
