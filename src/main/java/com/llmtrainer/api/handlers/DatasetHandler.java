package com.llmtrainer.api.handlers;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.llmtrainer.model.DatasetMetadata;
import com.llmtrainer.model.FileFormat;
import com.llmtrainer.storage.DataManager;
import com.llmtrainer.util.JsonUtil;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;

import java.io.*;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.*;

/**
 * Handles dataset-related API endpoints:
 * - POST /api/datasets/upload
 * - GET /api/datasets/{datasetId}
 * - DELETE /api/datasets/{datasetId}
 */
public class DatasetHandler implements HttpHandler {
    private final DataManager dataManager;
    private final Gson gson = new Gson();

    public DatasetHandler(DataManager dataManager) {
        this.dataManager = dataManager;
    }

    @Override
    public void handle(HttpExchange exchange) throws IOException {
        String method = exchange.getRequestMethod();
        String path = exchange.getRequestURI().getPath();

        try {
            if (method.equals("POST") && path.equals("/api/datasets/upload")) {
                handleUpload(exchange);
            } else if (method.equals("GET") && path.startsWith("/api/datasets/")) {
                handleGet(exchange);
            } else if (method.equals("DELETE") && path.startsWith("/api/datasets/")) {
                handleDelete(exchange);
            } else {
                sendResponse(exchange, 404, JsonUtil.errorResponse("Endpoint not found"));
            }
        } catch (Exception e) {
            e.printStackTrace();
            sendResponse(exchange, 500, JsonUtil.errorResponse("Internal server error: " + e.getMessage()));
        }
    }

    /**
     * Handle POST /api/datasets/upload
     * Expects multipart/form-data with 'file' and 'format' fields.
     */
    private void handleUpload(HttpExchange exchange) throws IOException {
        String contentType = exchange.getRequestHeaders().getFirst("Content-Type");

        if (contentType == null || !contentType.startsWith("multipart/form-data")) {
            sendResponse(exchange, 400, JsonUtil.errorResponse("Content-Type must be multipart/form-data"));
            return;
        }

        // Extract boundary from content type
        String boundary = extractBoundary(contentType);
        if (boundary == null) {
            sendResponse(exchange, 400, JsonUtil.errorResponse("Invalid multipart/form-data: no boundary"));
            return;
        }

        // Parse multipart form data
        Map<String, Object> formData = parseMultipartFormData(exchange.getRequestBody(), boundary);

        File uploadedFile = (File) formData.get("file");
        String formatStr = (String) formData.get("format");

        if (uploadedFile == null) {
            sendResponse(exchange, 400, JsonUtil.errorResponse("Missing 'file' field"));
            return;
        }

        if (formatStr == null) {
            sendResponse(exchange, 400, JsonUtil.errorResponse("Missing 'format' field"));
            return;
        }

        // Parse format
        FileFormat format;
        try {
            format = FileFormat.valueOf(formatStr.toUpperCase());
        } catch (IllegalArgumentException e) {
            sendResponse(exchange, 400, JsonUtil.errorResponse("Invalid format. Must be: jsonl, csv, or txt"));
            return;
        }

        try {
            // Store dataset
            DatasetMetadata metadata = dataManager.storeDataset(uploadedFile, format);

            // Build response
            Map<String, Object> responseData = new HashMap<>();
            responseData.put("datasetId", metadata.getDatasetId());
            responseData.put("filename", metadata.getOriginalFilename());
            responseData.put("format", metadata.getFileFormat().name().toLowerCase());
            responseData.put("fileSize", metadata.getFileSize());
            responseData.put("rowCount", metadata.getRowCount());

            sendResponse(exchange, 200, JsonUtil.successResponse(responseData));
        } catch (IllegalArgumentException e) {
            sendResponse(exchange, 400, JsonUtil.errorResponse(e.getMessage()));
        } catch (IOException e) {
            sendResponse(exchange, 500, JsonUtil.errorResponse("Failed to store dataset: " + e.getMessage()));
        } finally {
            // Clean up temporary file
            if (uploadedFile != null && uploadedFile.exists()) {
                uploadedFile.delete();
            }
        }
    }

    /**
     * Handle GET /api/datasets/{datasetId}
     */
    private void handleGet(HttpExchange exchange) throws IOException {
        String path = exchange.getRequestURI().getPath();
        String datasetId = path.substring("/api/datasets/".length());

        DatasetMetadata metadata = dataManager.getDatasetMetadata(datasetId);
        if (metadata == null) {
            sendResponse(exchange, 404, JsonUtil.errorResponse("Dataset not found"));
            return;
        }

        Map<String, Object> responseData = new HashMap<>();
        responseData.put("datasetId", metadata.getDatasetId());
        responseData.put("originalFilename", metadata.getOriginalFilename());
        responseData.put("fileFormat", metadata.getFileFormat().name());
        responseData.put("filePath", metadata.getFilePath());
        responseData.put("fileSize", metadata.getFileSize());
        responseData.put("rowCount", metadata.getRowCount());
        responseData.put("uploadedAt", metadata.getUploadedAt().toString());

        sendResponse(exchange, 200, JsonUtil.successResponse(responseData));
    }

    /**
     * Handle DELETE /api/datasets/{datasetId}
     */
    private void handleDelete(HttpExchange exchange) throws IOException {
        String path = exchange.getRequestURI().getPath();
        String datasetId = path.substring("/api/datasets/".length());

        boolean deleted = dataManager.deleteDataset(datasetId);
        if (!deleted) {
            sendResponse(exchange, 404, JsonUtil.errorResponse("Dataset not found"));
            return;
        }

        Map<String, String> responseData = new HashMap<>();
        responseData.put("message", "Dataset deleted successfully");

        sendResponse(exchange, 200, JsonUtil.successResponse(responseData));
    }

    /**
     * Extract boundary from Content-Type header.
     */
    private String extractBoundary(String contentType) {
        String[] parts = contentType.split(";");
        for (String part : parts) {
            String trimmed = part.trim();
            if (trimmed.startsWith("boundary=")) {
                return trimmed.substring("boundary=".length());
            }
        }
        return null;
    }

    /**
     * Parse multipart/form-data from input stream.
     * Returns a map with 'file' (File) and 'format' (String).
     */
    private Map<String, Object> parseMultipartFormData(InputStream inputStream, String boundary) throws IOException {
        Map<String, Object> result = new HashMap<>();
        
        // Read all bytes first
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        byte[] buffer = new byte[8192];
        int bytesRead;
        while ((bytesRead = inputStream.read(buffer)) != -1) {
            baos.write(buffer, 0, bytesRead);
        }
        byte[] allBytes = baos.toByteArray();
        
        // Convert boundary to bytes
        String boundaryDelimiter = "--" + boundary;
        byte[] boundaryBytes = boundaryDelimiter.getBytes(StandardCharsets.UTF_8);
        byte[] crlfBytes = "\r\n".getBytes(StandardCharsets.UTF_8);
        
        int pos = 0;
        while (pos < allBytes.length) {
            // Find next boundary
            int boundaryStart = indexOf(allBytes, boundaryBytes, pos);
            if (boundaryStart == -1) break;
            
            pos = boundaryStart + boundaryBytes.length;
            
            // Skip CRLF after boundary
            if (pos + 2 <= allBytes.length && allBytes[pos] == '\r' && allBytes[pos + 1] == '\n') {
                pos += 2;
            }
            
            // Check if this is the final boundary
            if (pos + 2 <= allBytes.length && allBytes[pos] == '-' && allBytes[pos + 1] == '-') {
                break;
            }
            
            // Read headers until blank line
            Map<String, String> headers = new HashMap<>();
            while (pos < allBytes.length) {
                int lineEnd = indexOf(allBytes, crlfBytes, pos);
                if (lineEnd == -1) break;
                
                if (lineEnd == pos) {
                    // Blank line - end of headers
                    pos = lineEnd + 2;
                    break;
                }
                
                String headerLine = new String(allBytes, pos, lineEnd - pos, StandardCharsets.UTF_8);
                int colonIndex = headerLine.indexOf(':');
                if (colonIndex > 0) {
                    String headerName = headerLine.substring(0, colonIndex).trim().toLowerCase();
                    String headerValue = headerLine.substring(colonIndex + 1).trim();
                    headers.put(headerName, headerValue);
                }
                
                pos = lineEnd + 2;
            }
            
            // Parse Content-Disposition
            String contentDisposition = headers.get("content-disposition");
            if (contentDisposition == null) continue;
            
            String fieldName = extractFieldName(contentDisposition);
            String fileName = extractFileName(contentDisposition);
            
            if (fieldName == null) continue;
            
            // Find the end of this part's content (next boundary)
            int nextBoundary = indexOf(allBytes, ("\r\n" + boundaryDelimiter).getBytes(StandardCharsets.UTF_8), pos);
            if (nextBoundary == -1) {
                nextBoundary = allBytes.length;
            }
            
            // Extract content
            byte[] content = Arrays.copyOfRange(allBytes, pos, nextBoundary);
            
            if (fieldName.equals("file") && fileName != null) {
                // Write file content to temp file
                File tempFile = File.createTempFile("upload-", fileName);
                try (FileOutputStream fos = new FileOutputStream(tempFile)) {
                    fos.write(content);
                }
                result.put("file", tempFile);
            } else if (fieldName.equals("format")) {
                // Read format value as string
                String value = new String(content, StandardCharsets.UTF_8).trim();
                result.put("format", value);
            }
            
            pos = nextBoundary;
        }
        
        return result;
    }
    
    /**
     * Find byte pattern in byte array, starting from offset.
     */
    private int indexOf(byte[] array, byte[] pattern, int start) {
        outer: for (int i = start; i <= array.length - pattern.length; i++) {
            for (int j = 0; j < pattern.length; j++) {
                if (array[i + j] != pattern[j]) {
                    continue outer;
                }
            }
            return i;
        }
        return -1;
    }

    private String extractFieldName(String contentDisposition) {
        String[] parts = contentDisposition.split(";");
        for (String part : parts) {
            String trimmed = part.trim();
            if (trimmed.startsWith("name=")) {
                String value = trimmed.substring("name=".length());
                return value.replace("\"", "").trim();
            }
        }
        return null;
    }

    private String extractFileName(String contentDisposition) {
        String[] parts = contentDisposition.split(";");
        for (String part : parts) {
            String trimmed = part.trim();
            if (trimmed.startsWith("filename=")) {
                String value = trimmed.substring("filename=".length());
                return value.replace("\"", "").trim();
            }
        }
        return null;
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
