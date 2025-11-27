package com.llmtrainer.api.handlers;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.llmtrainer.logging.LogStore;
import com.google.gson.reflect.TypeToken;
import java.lang.reflect.Type;
import com.llmtrainer.logging.TrainingMetrics;
import com.llmtrainer.model.JobStatus;
import com.llmtrainer.model.TrainingJob;
import com.llmtrainer.orchestrator.ProcessOrchestrator;
import com.llmtrainer.queue.JobQueueManager;
import com.llmtrainer.storage.DataManager;
import com.llmtrainer.util.JsonUtil;
import com.llmtrainer.util.UuidGenerator;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/**
 * Handles job-related API endpoints.
 */
public class JobHandler implements HttpHandler {
    private final JobQueueManager queueManager;
    private final DataManager dataManager;
    private final LogStore logStore;
    private final ProcessOrchestrator orchestrator;
    private final Gson gson = new Gson();

    public JobHandler(JobQueueManager queueManager, DataManager dataManager,
                     LogStore logStore, ProcessOrchestrator orchestrator) {
        this.queueManager = queueManager;
        this.dataManager = dataManager;
        this.logStore = logStore;
        this.orchestrator = orchestrator;
    }

    @Override
    public void handle(HttpExchange exchange) throws IOException {
        String method = exchange.getRequestMethod();
        String path = exchange.getRequestURI().getPath();

        try {
            if (method.equals("POST") && path.equals("/api/jobs/create")) {
                handleCreateJob(exchange);
            } else if (method.equals("POST") && path.matches("/api/jobs/.+/start")) {
                handleStartJob(exchange);
            } else if (method.equals("POST") && path.matches("/api/jobs/.+/pause")) {
                handlePauseJob(exchange);
            } else if (method.equals("POST") && path.matches("/api/jobs/.+/resume")) {
                handleResumeJob(exchange);
            } else if (method.equals("POST") && path.matches("/api/jobs/.+/cancel")) {
                handleCancelJob(exchange);
            } else if (method.equals("GET") && path.matches("/api/jobs/.+/status")) {
                handleGetStatus(exchange);
            } else if (method.equals("GET") && path.matches("/api/jobs/.+/logs")) {
                handleGetLogs(exchange);
            } else if (method.equals("GET") && path.matches("/api/jobs/.+/metrics")) {
                handleGetMetrics(exchange);
            } else if (method.equals("GET") && path.equals("/api/jobs/queue")) {
                handleGetQueue(exchange);
            } else if (method.equals("POST") && path.matches("/api/jobs/.+/convert-gguf")) {
                handleConvertGguf(exchange);
            } else if (method.equals("GET") && path.matches("/api/jobs/.+/conversion-status")) {
                handleGetConversionStatus(exchange);
            } else if (method.equals("GET") && path.matches("/api/jobs/.+/download-gguf")) {
                handleDownloadGguf(exchange);
            } else {
                sendResponse(exchange, 404, JsonUtil.errorResponse("Endpoint not found"));
            }
        } catch (Exception e) {
            e.printStackTrace();
            sendResponse(exchange, 500, JsonUtil.errorResponse("Internal server error: " + e.getMessage()));
        }
    }

    /**
     * POST /api/jobs/create
     */
    private void handleCreateJob(HttpExchange exchange) throws IOException {
        String body = readRequestBody(exchange);
        JsonObject json = gson.fromJson(body, JsonObject.class);

        // Validate required fields
        if (!json.has("projectName") || !json.has("datasetId") ||
            !json.has("baseModel") || !json.has("hyperparameters")) {
            sendResponse(exchange, 400, JsonUtil.errorResponse("Missing required fields"));
            return;
        }

        String projectName = json.get("projectName").getAsString();
        String datasetId = json.get("datasetId").getAsString();
        String baseModel = json.get("baseModel").getAsString();
    Type mapType = new TypeToken<Map<String, Object>>(){}.getType();
    Map<String, Object> hyperparameters = gson.fromJson(json.get("hyperparameters"), mapType);

        // Validate dataset exists
        if (!dataManager.datasetExists(datasetId)) {
            sendResponse(exchange, 404, JsonUtil.errorResponse("Dataset not found"));
            return;
        }

        String datasetPath = dataManager.getDatasetMetadata(datasetId).getFilePath();

        // Create job
        String jobId = UuidGenerator.generate();
        TrainingJob job = new TrainingJob(jobId, projectName, datasetPath, baseModel, hyperparameters);

        // Enqueue job
        queueManager.enqueueJob(job);

        // Build response
        Map<String, Object> responseData = new HashMap<>();
        responseData.put("jobId", jobId);
        responseData.put("status", job.getStatus().name());
        responseData.put("createdAt", job.getCreatedAt().toString());

        sendResponse(exchange, 200, JsonUtil.successResponse(responseData));
    }

    /**
     * POST /api/jobs/{jobId}/start
     */
    private void handleStartJob(HttpExchange exchange) throws IOException {
        String jobId = extractJobId(exchange.getRequestURI().getPath());
        TrainingJob job = queueManager.getJob(jobId);

        if (job == null) {
            sendResponse(exchange, 404, JsonUtil.errorResponse("Job not found"));
            return;
        }

        if (job.getStatus() != JobStatus.QUEUED) {
            sendResponse(exchange, 400, JsonUtil.errorResponse("Job is not in QUEUED state"));
            return;
        }

        // Start training
        try {
            job.setStatus(JobStatus.RUNNING);
            queueManager.setCurrentRunningJob(job);
            orchestrator.startTraining(job);

            Map<String, Object> responseData = new HashMap<>();
            responseData.put("jobId", jobId);
            responseData.put("status", job.getStatus().name());
            responseData.put("startedAt", job.getStartedAt().toString());

            sendResponse(exchange, 200, JsonUtil.successResponse(responseData));
        } catch (Exception e) {
            job.setStatus(JobStatus.FAILED);
            sendResponse(exchange, 500, JsonUtil.errorResponse("Failed to start training: " + e.getMessage()));
        }
    }

    /**
     * POST /api/jobs/{jobId}/pause
     */
    private void handlePauseJob(HttpExchange exchange) throws IOException {
        String jobId = extractJobId(exchange.getRequestURI().getPath());
        TrainingJob job = queueManager.getJob(jobId);

        if (job == null) {
            sendResponse(exchange, 404, JsonUtil.errorResponse("Job not found"));
            return;
        }

        if (job.getStatus() != JobStatus.RUNNING) {
            sendResponse(exchange, 400, JsonUtil.errorResponse("Job is not running"));
            return;
        }

        boolean paused = orchestrator.pauseProcess(jobId);
        if (paused) {
            queueManager.pauseJob(jobId);

            Map<String, Object> responseData = new HashMap<>();
            responseData.put("jobId", jobId);
            responseData.put("status", JobStatus.PAUSED.name());

            sendResponse(exchange, 200, JsonUtil.successResponse(responseData));
        } else {
            sendResponse(exchange, 500, JsonUtil.errorResponse("Failed to pause job"));
        }
    }

    /**
     * POST /api/jobs/{jobId}/resume
     */
    private void handleResumeJob(HttpExchange exchange) throws IOException {
        String jobId = extractJobId(exchange.getRequestURI().getPath());
        TrainingJob job = queueManager.getJob(jobId);

        if (job == null) {
            sendResponse(exchange, 404, JsonUtil.errorResponse("Job not found"));
            return;
        }

        if (job.getStatus() != JobStatus.PAUSED) {
            sendResponse(exchange, 400, JsonUtil.errorResponse("Job is not paused"));
            return;
        }

        boolean resumed = orchestrator.resumeProcess(jobId);
        if (resumed) {
            queueManager.resumeJob(jobId);

            Map<String, Object> responseData = new HashMap<>();
            responseData.put("jobId", jobId);
            responseData.put("status", JobStatus.RUNNING.name());

            sendResponse(exchange, 200, JsonUtil.successResponse(responseData));
        } else {
            sendResponse(exchange, 500, JsonUtil.errorResponse("Failed to resume job"));
        }
    }

    /**
     * POST /api/jobs/{jobId}/cancel
     */
    private void handleCancelJob(HttpExchange exchange) throws IOException {
        String jobId = extractJobId(exchange.getRequestURI().getPath());
        TrainingJob job = queueManager.getJob(jobId);

        if (job == null) {
            sendResponse(exchange, 404, JsonUtil.errorResponse("Job not found"));
            return;
        }

        // Kill process if running
        if (job.getStatus() == JobStatus.RUNNING || job.getStatus() == JobStatus.PAUSED) {
            orchestrator.killProcess(jobId);
        }

        queueManager.cancelJob(jobId);

        Map<String, Object> responseData = new HashMap<>();
        responseData.put("jobId", jobId);
        responseData.put("status", JobStatus.CANCELLED.name());

        sendResponse(exchange, 200, JsonUtil.successResponse(responseData));
    }

    /**
     * GET /api/jobs/{jobId}/status
     */
    private void handleGetStatus(HttpExchange exchange) throws IOException {
        String jobId = extractJobId(exchange.getRequestURI().getPath());
        TrainingJob job = queueManager.getJob(jobId);

        if (job == null) {
            sendResponse(exchange, 404, JsonUtil.errorResponse("Job not found"));
            return;
        }

        Map<String, Object> responseData = new HashMap<>();
        responseData.put("jobId", job.getJobId());
        responseData.put("projectName", job.getProjectName());
        responseData.put("status", job.getStatus().name());
        responseData.put("datasetPath", job.getDatasetPath());
        responseData.put("baseModel", job.getBaseModel());
        responseData.put("hyperparameters", job.getHyperparameters());
        responseData.put("createdAt", job.getCreatedAt().toString());
        responseData.put("startedAt", job.getStartedAt() != null ? job.getStartedAt().toString() : null);
        responseData.put("completedAt", job.getCompletedAt() != null ? job.getCompletedAt().toString() : null);
        responseData.put("outputModelPath", job.getOutputModelPath());
        responseData.put("ggufPath", job.getGgufPath());

        sendResponse(exchange, 200, JsonUtil.successResponse(responseData));
    }

    /**
     * GET /api/jobs/{jobId}/logs
     */
    private void handleGetLogs(HttpExchange exchange) throws IOException {
        String jobId = extractJobId(exchange.getRequestURI().getPath());
        TrainingJob job = queueManager.getJob(jobId);

        if (job == null) {
            sendResponse(exchange, 404, JsonUtil.errorResponse("Job not found"));
            return;
        }

        // Parse query parameter for number of lines
        String query = exchange.getRequestURI().getQuery();
        int lines = 100; // default
        if (query != null && query.contains("lines=")) {
            try {
                String linesStr = query.split("lines=")[1].split("&")[0];
                lines = Integer.parseInt(linesStr);
            } catch (Exception e) {
                // Use default
            }
        }

        List<String> logs = logStore.getRecentLogs(jobId, lines);

        Map<String, Object> responseData = new HashMap<>();
        responseData.put("jobId", jobId);
        responseData.put("logs", logs);

        sendResponse(exchange, 200, JsonUtil.successResponse(responseData));
    }

    /**
     * GET /api/jobs/{jobId}/metrics
     */
    private void handleGetMetrics(HttpExchange exchange) throws IOException {
        String jobId = extractJobId(exchange.getRequestURI().getPath());
        TrainingJob job = queueManager.getJob(jobId);

        if (job == null) {
            sendResponse(exchange, 404, JsonUtil.errorResponse("Job not found"));
            return;
        }

        TrainingMetrics metrics = logStore.getCurrentMetrics(jobId);

        Map<String, Object> responseData = new HashMap<>();
        responseData.put("jobId", jobId);

        if (metrics != null) {
            responseData.put("loss", metrics.getLoss());
            responseData.put("epoch", metrics.getCurrentEpoch());
            responseData.put("totalEpochs", metrics.getTotalEpochs());
            responseData.put("step", metrics.getCurrentStep());
            responseData.put("totalSteps", metrics.getTotalSteps());
            responseData.put("samplesPerSecond", metrics.getSamplesPerSecond());
            responseData.put("estimatedTimeRemaining", metrics.getEstimatedTimeRemaining());
        } else {
            responseData.put("loss", null);
            responseData.put("epoch", null);
            responseData.put("step", null);
            responseData.put("samplesPerSecond", null);
            responseData.put("estimatedTimeRemaining", null);
        }

        sendResponse(exchange, 200, JsonUtil.successResponse(responseData));
    }

    /**
     * GET /api/jobs/queue
     */
    private void handleGetQueue(HttpExchange exchange) throws IOException {
        List<TrainingJob> jobs = queueManager.getAllJobs();

        List<Map<String, Object>> jobsList = new ArrayList<>();
        for (TrainingJob job : jobs) {
            Map<String, Object> jobData = new HashMap<>();
            jobData.put("jobId", job.getJobId());
            jobData.put("projectName", job.getProjectName());
            jobData.put("status", job.getStatus().name());
            jobData.put("createdAt", job.getCreatedAt().toString());
            jobsList.add(jobData);
        }

        Map<String, Object> responseData = new HashMap<>();
        responseData.put("jobs", jobsList);

        sendResponse(exchange, 200, JsonUtil.successResponse(responseData));
    }

    /**
     * POST /api/jobs/{jobId}/convert-gguf
     */
    private void handleConvertGguf(HttpExchange exchange) throws IOException {
        String jobId = extractJobId(exchange.getRequestURI().getPath());
        TrainingJob job = queueManager.getJob(jobId);

        if (job == null) {
            sendResponse(exchange, 404, JsonUtil.errorResponse("Job not found"));
            return;
        }

        if (job.getStatus() != JobStatus.COMPLETED) {
            sendResponse(exchange, 400, JsonUtil.errorResponse("Training must be completed before conversion"));
            return;
        }

        // Start conversion
        try {
            orchestrator.startConversion(job);

            Map<String, Object> responseData = new HashMap<>();
            responseData.put("jobId", jobId);
            responseData.put("message", "GGUF conversion started");
            responseData.put("conversionStatus", "RUNNING");

            sendResponse(exchange, 200, JsonUtil.successResponse(responseData));
        } catch (Exception e) {
            sendResponse(exchange, 500, JsonUtil.errorResponse("Failed to start conversion: " + e.getMessage()));
        }
    }

    /**
     * GET /api/jobs/{jobId}/download-gguf
     */
    private void handleDownloadGguf(HttpExchange exchange) throws IOException {
        String jobId = extractJobId(exchange.getRequestURI().getPath());
        TrainingJob job = queueManager.getJob(jobId);

        if (job == null) {
            sendResponse(exchange, 404, JsonUtil.errorResponse("Job not found"));
            return;
        }

        if (job.getStatus() != JobStatus.COMPLETED) {
            sendResponse(exchange, 400, JsonUtil.errorResponse("Training must be completed before download"));
            return;
        }

        String ggufPath = job.getGgufPath();
        if (ggufPath == null) {
            sendResponse(exchange, 400, JsonUtil.errorResponse("GGUF conversion not started or in progress"));
            return;
        }

        File ggufFile = new File(ggufPath);
        if (!ggufFile.exists()) {
            sendResponse(exchange, 404, JsonUtil.errorResponse("GGUF file not found"));
            return;
        }

        // Stream file to response
        exchange.getResponseHeaders().set("Content-Type", "application/octet-stream");
        exchange.getResponseHeaders().set("Content-Disposition", "attachment; filename=\"" + jobId + ".gguf\"");
        exchange.sendResponseHeaders(200, ggufFile.length());

        try (OutputStream os = exchange.getResponseBody();
             FileInputStream fis = new FileInputStream(ggufFile)) {
            byte[] buffer = new byte[8192];
            int bytesRead;
            while ((bytesRead = fis.read(buffer)) != -1) {
                os.write(buffer, 0, bytesRead);
            }
        }
    }

    /**
     * GET /api/jobs/{jobId}/conversion-status
     * Provides detailed status about GGUF conversion progress for low-RAM environments.
     */
    private void handleGetConversionStatus(HttpExchange exchange) throws IOException {
        String jobId = extractJobId(exchange.getRequestURI().getPath());
        TrainingJob job = queueManager.getJob(jobId);

        if (job == null) {
            sendResponse(exchange, 404, JsonUtil.errorResponse("Job not found"));
            return;
        }

        // Basic preconditions
        boolean trainingCompleted = job.getStatus() == JobStatus.COMPLETED;
        String ggufPath = job.getGgufPath();
        boolean fileExists = false;
        long fileSize = 0L;
        if (ggufPath != null) {
            var f = new java.io.File(ggufPath);
            if (f.exists()) {
                fileExists = true;
                fileSize = f.length();
            }
        }

        // Inspect logs for conversion lifecycle markers
        String conversionJobId = jobId + "-conversion";
        var recentConvLogs = logStore.getRecentLogs(conversionJobId, 200); // last 200 lines
        boolean conversionStarted = false;
        boolean conversionSucceeded = false;
        boolean conversionFailed = false;
        for (String line : recentConvLogs) {
            if (line.contains("Starting GGUF conversion")) {
                conversionStarted = true;
            }
            if (line.contains("GGUF conversion completed successfully")) {
                conversionSucceeded = true;
            }
            if (line.contains("GGUF conversion failed")) {
                conversionFailed = true;
            }
        }

        String phase;
        if (!trainingCompleted) {
            phase = "TRAINING";
        } else if (!conversionStarted && ggufPath == null) {
            phase = "READY_FOR_CONVERSION";
        } else if (conversionStarted && !conversionSucceeded && !conversionFailed) {
            phase = "CONVERTING";
        } else if (conversionSucceeded && fileExists) {
            phase = "CONVERSION_COMPLETED";
        } else if (conversionFailed) {
            phase = "CONVERSION_FAILED";
        } else if (ggufPath != null && !fileExists) {
            phase = "CONVERSION_FILE_MISSING";
        } else {
            phase = "UNKNOWN";
        }

        Map<String, Object> responseData = new HashMap<>();
        responseData.put("jobId", jobId);
        responseData.put("trainingCompleted", trainingCompleted);
        responseData.put("conversionStarted", conversionStarted);
        responseData.put("conversionSucceeded", conversionSucceeded);
        responseData.put("conversionFailed", conversionFailed);
        responseData.put("phase", phase);
        responseData.put("ggufPath", ggufPath);
        responseData.put("fileExists", fileExists);
        responseData.put("fileSizeBytes", fileSize);
        responseData.put("recentConversionLogs", recentConvLogs);

        sendResponse(exchange, 200, JsonUtil.successResponse(responseData));
    }

    /**
     * Extract jobId from path like /api/jobs/{jobId}/action
     */
    private String extractJobId(String path) {
        String[] parts = path.split("/");
        if (parts.length >= 4) {
            return parts[3]; // /api/jobs/{jobId}/...
        }
        return null;
    }

    /**
     * Read request body as string.
     */
    private String readRequestBody(HttpExchange exchange) throws IOException {
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(exchange.getRequestBody(), StandardCharsets.UTF_8))) {
            StringBuilder body = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                body.append(line);
            }
            return body.toString();
        }
    }

    /**
     * Send HTTP response.
     */
    private void sendResponse(HttpExchange exchange, int statusCode, String response) throws IOException {
        byte[] bytes = response.getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().set("Content-Type", "application/json");
        exchange.sendResponseHeaders(statusCode, bytes.length);
        try (OutputStream os = exchange.getResponseBody()) {
            os.write(bytes);
        }
    }
}
