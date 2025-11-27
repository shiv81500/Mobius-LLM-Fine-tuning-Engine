package com.llmtrainer.api;

import com.llmtrainer.api.handlers.DatasetHandler;
import com.llmtrainer.api.handlers.JobHandler;
import com.llmtrainer.logging.LogStore;
import com.llmtrainer.orchestrator.ProcessOrchestrator;
import com.llmtrainer.queue.JobQueueManager;
import com.llmtrainer.storage.DataManager;
import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.util.concurrent.Executors;

/**
 * HTTP API server using Java's built-in HttpServer.
 * Listens on localhost:8080 and provides REST API for GUI.
 */
public class ApiServer {
    private final HttpServer server;
    private final int port;

    public ApiServer(int port, JobQueueManager queueManager, DataManager dataManager,
                    LogStore logStore, ProcessOrchestrator orchestrator) throws IOException {
        this.port = port;
        this.server = HttpServer.create(new InetSocketAddress("localhost", port), 0);

        // Create handlers
        DatasetHandler datasetHandler = new DatasetHandler(dataManager);
        JobHandler jobHandler = new JobHandler(queueManager, dataManager, logStore, orchestrator);

        // Register contexts (routes)
        server.createContext("/api/datasets", datasetHandler);
        server.createContext("/api/jobs", jobHandler);

        // Set thread pool executor
        server.setExecutor(Executors.newFixedThreadPool(10));
    }

    /**
     * Start the HTTP server.
     */
    public void start() {
        server.start();
        System.out.println("LLM Training Backend running on http://localhost:" + port);
    }

    /**
     * Stop the HTTP server.
     */
    public void stop() {
        server.stop(2); // 2 second delay for graceful shutdown
        System.out.println("HTTP server stopped");
    }
}
