package com.llmtrainer.storage;

import com.llmtrainer.model.DatasetMetadata;
import com.llmtrainer.model.FileFormat;
import com.llmtrainer.util.UuidGenerator;

import java.io.*;
import java.nio.file.*;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.locks.ReentrantLock;

/**
 * Manages dataset storage using a HashMap for O(1) lookup.
 */
public class DataManager {
    private final Map<String, DatasetMetadata> datasetMap;
    private final String datasetsDir;
    private final ReentrantLock lock;

    public DataManager(String baseDataDir) {
        this.datasetMap = new HashMap<>();
        this.datasetsDir = baseDataDir + "/datasets";
        this.lock = new ReentrantLock();

        // Create datasets directory if it doesn't exist
        try {
            Files.createDirectories(Paths.get(datasetsDir));
        } catch (IOException e) {
            throw new RuntimeException("Failed to create datasets directory: " + e.getMessage(), e);
        }
    }

    /**
     * Store an uploaded dataset file.
     * O(1) insertion into HashMap.
     *
     * @param uploadedFile The file to store
     * @param format The file format (JSONL, CSV, or TXT)
     * @return DatasetMetadata for the stored file
     * @throws IOException if file operations fail
     */
    public DatasetMetadata storeDataset(File uploadedFile, FileFormat format) throws IOException {
        lock.lock();
        try {
            // Generate unique dataset ID
            String datasetId = UuidGenerator.generate();

            // Determine file extension based on format
            String extension = format.name().toLowerCase();
            String targetFileName = datasetId + "." + extension;
            String targetPath = datasetsDir + "/" + targetFileName;

            // Validate the file before storing
            int rowCount = FileValidator.validateAndCountRows(uploadedFile, format);

            // Copy file to datasets directory
            Files.copy(uploadedFile.toPath(), Paths.get(targetPath), StandardCopyOption.REPLACE_EXISTING);

            // Create metadata
            DatasetMetadata metadata = new DatasetMetadata(
                datasetId,
                uploadedFile.getName(),
                format,
                targetPath,
                uploadedFile.length(),
                rowCount
            );

            // Store in HashMap
            datasetMap.put(datasetId, metadata);

            return metadata;
        } finally {
            lock.unlock();
        }
    }

    /**
     * Get dataset metadata by ID.
     * O(1) average case lookup.
     */
    public DatasetMetadata getDatasetMetadata(String datasetId) {
        lock.lock();
        try {
            return datasetMap.get(datasetId);
        } finally {
            lock.unlock();
        }
    }

    /**
     * Validate that a dataset exists and is accessible.
     */
    public boolean validateDataset(String datasetId) {
        lock.lock();
        try {
            DatasetMetadata metadata = datasetMap.get(datasetId);
            if (metadata == null) {
                return false;
            }

            // Check if file still exists on disk
            File file = new File(metadata.getFilePath());
            return file.exists() && file.canRead();
        } finally {
            lock.unlock();
        }
    }

    /**
     * Delete a dataset (metadata and file).
     */
    public boolean deleteDataset(String datasetId) {
        lock.lock();
        try {
            DatasetMetadata metadata = datasetMap.get(datasetId);
            if (metadata == null) {
                return false;
            }

            // Delete file from disk
            File file = new File(metadata.getFilePath());
            if (file.exists()) {
                file.delete();
            }

            // Remove from HashMap
            datasetMap.remove(datasetId);

            return true;
        } finally {
            lock.unlock();
        }
    }

    /**
     * Get all stored datasets.
     */
    public Map<String, DatasetMetadata> getAllDatasets() {
        lock.lock();
        try {
            return new HashMap<>(datasetMap);
        } finally {
            lock.unlock();
        }
    }

    /**
     * Check if a dataset exists.
     */
    public boolean datasetExists(String datasetId) {
        lock.lock();
        try {
            return datasetMap.containsKey(datasetId);
        } finally {
            lock.unlock();
        }
    }
}
