package com.llmtrainer.storage;

import com.llmtrainer.model.FileFormat;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * Validates uploaded training data files.
 */
public class FileValidator {

    private static final long MAX_FILE_SIZE = 10L * 1024 * 1024 * 1024; // 10 GB

    /**
     * Validate a dataset file and count rows.
     * Returns the number of rows/examples in the file.
     * Throws IllegalArgumentException if validation fails.
     */
    public static int validateAndCountRows(File file, FileFormat format) throws IOException {
        // Check file size
        long fileSize = file.length();
        if (fileSize > MAX_FILE_SIZE) {
            throw new IllegalArgumentException("File exceeds 10GB limit");
        }

        if (fileSize == 0) {
            throw new IllegalArgumentException("File is empty");
        }

        // Validate and count based on format
        switch (format) {
            case JSONL:
                return validateJsonl(file);
            case CSV:
                return validateCsv(file);
            case TXT:
                return validateTxt(file);
            default:
                throw new IllegalArgumentException("Unsupported file format: " + format);
        }
    }

    /**
     * Validate JSONL file format.
     * Each line should be valid JSON.
     */
    private static int validateJsonl(File file) throws IOException {
        int lineCount = 0;
        try (BufferedReader reader = new BufferedReader(new FileReader(file))) {
            String line;
            while ((line = reader.readLine()) != null) {
                line = line.trim();
                if (!line.isEmpty()) {
                    // Basic JSON validation - should start with { and end with }
                    if (!line.startsWith("{") || !line.endsWith("}")) {
                        throw new IllegalArgumentException("Invalid JSONL format at line " + (lineCount + 1) +
                                                         ". Each line must be a valid JSON object.");
                    }
                    lineCount++;
                }
            }
        }

        if (lineCount == 0) {
            throw new IllegalArgumentException("JSONL file contains no valid data");
        }

        return lineCount;
    }

    /**
     * Validate CSV file format.
     * Should have headers and at least one data row.
     */
    private static int validateCsv(File file) throws IOException {
        int lineCount = 0;
        try (BufferedReader reader = new BufferedReader(new FileReader(file))) {
            String headerLine = reader.readLine();
            if (headerLine == null || headerLine.trim().isEmpty()) {
                throw new IllegalArgumentException("CSV file has no header row");
            }

            String line;
            while ((line = reader.readLine()) != null) {
                if (!line.trim().isEmpty()) {
                    lineCount++;
                }
            }
        }

        if (lineCount == 0) {
            throw new IllegalArgumentException("CSV file contains no data rows");
        }

        return lineCount;
    }

    /**
     * Validate TXT file format.
     * Just count non-empty lines.
     */
    private static int validateTxt(File file) throws IOException {
        int lineCount = 0;
        try (BufferedReader reader = new BufferedReader(new FileReader(file))) {
            String line;
            while ((line = reader.readLine()) != null) {
                if (!line.trim().isEmpty()) {
                    lineCount++;
                }
            }
        }

        if (lineCount == 0) {
            throw new IllegalArgumentException("TXT file is empty");
        }

        // For text files, we'll chunk them, so estimate chunks
        // Assuming ~2048 char chunks
        return Math.max(1, lineCount / 10);
    }
}
