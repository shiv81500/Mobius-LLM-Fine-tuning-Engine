package com.llmtrainer.util;

import java.util.UUID;

/**
 * Utility class for generating unique identifiers.
 */
public class UuidGenerator {

    /**
     * Generate a random UUID string.
     * @return A UUID string in the format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
     */
    public static String generate() {
        return UUID.randomUUID().toString();
    }
}
