package com.llmtrainer.model;

import java.time.LocalDateTime;

/**
 * Metadata for uploaded training datasets.
 */
public class DatasetMetadata {
    private String datasetId;
    private String originalFilename;
    private FileFormat fileFormat;
    private String filePath;
    private long fileSize;
    private int rowCount;
    private LocalDateTime uploadedAt;

    public DatasetMetadata(String datasetId, String originalFilename, FileFormat fileFormat,
                          String filePath, long fileSize, int rowCount) {
        this.datasetId = datasetId;
        this.originalFilename = originalFilename;
        this.fileFormat = fileFormat;
        this.filePath = filePath;
        this.fileSize = fileSize;
        this.rowCount = rowCount;
        this.uploadedAt = LocalDateTime.now();
    }

    // Getters and setters
    public String getDatasetId() {
        return datasetId;
    }

    public void setDatasetId(String datasetId) {
        this.datasetId = datasetId;
    }

    public String getOriginalFilename() {
        return originalFilename;
    }

    public void setOriginalFilename(String originalFilename) {
        this.originalFilename = originalFilename;
    }

    public FileFormat getFileFormat() {
        return fileFormat;
    }

    public void setFileFormat(FileFormat fileFormat) {
        this.fileFormat = fileFormat;
    }

    public String getFilePath() {
        return filePath;
    }

    public void setFilePath(String filePath) {
        this.filePath = filePath;
    }

    public long getFileSize() {
        return fileSize;
    }

    public void setFileSize(long fileSize) {
        this.fileSize = fileSize;
    }

    public int getRowCount() {
        return rowCount;
    }

    public void setRowCount(int rowCount) {
        this.rowCount = rowCount;
    }

    public LocalDateTime getUploadedAt() {
        return uploadedAt;
    }

    public void setUploadedAt(LocalDateTime uploadedAt) {
        this.uploadedAt = uploadedAt;
    }
}
