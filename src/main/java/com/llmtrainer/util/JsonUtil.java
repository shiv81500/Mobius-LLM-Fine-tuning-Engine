package com.llmtrainer.util;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonSyntaxException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

/**
 * Utility class for JSON serialization and deserialization using Gson.
 */
public class JsonUtil {
    private static final Gson gson = new GsonBuilder()
            .registerTypeAdapter(LocalDateTime.class, new LocalDateTimeAdapter())
            .setPrettyPrinting()
            .create();

    /**
     * Convert an object to JSON string.
     */
    public static String toJson(Object obj) {
        return gson.toJson(obj);
    }

    /**
     * Parse JSON string to an object of specified class.
     */
    public static <T> T fromJson(String json, Class<T> clazz) throws JsonSyntaxException {
        return gson.fromJson(json, clazz);
    }

    /**
     * Create a simple JSON response with status and data.
     */
    public static String successResponse(Object data) {
        Response response = new Response("success", data, null);
        return toJson(response);
    }

    /**
     * Create a simple JSON error response.
     */
    public static String errorResponse(String error) {
        Response response = new Response("error", null, error);
        return toJson(response);
    }

    /**
     * Internal class for standard API responses.
     */
    private static class Response {
        private final String status;
        private final Object data;
        private final String error;

        public Response(String status, Object data, String error) {
            this.status = status;
            this.data = data;
            this.error = error;
        }
    }

    /**
     * Adapter for LocalDateTime serialization/deserialization.
     */
    private static class LocalDateTimeAdapter extends com.google.gson.TypeAdapter<LocalDateTime> {
        private static final DateTimeFormatter formatter = DateTimeFormatter.ISO_LOCAL_DATE_TIME;

        @Override
        public void write(com.google.gson.stream.JsonWriter out, LocalDateTime value) throws java.io.IOException {
            if (value == null) {
                out.nullValue();
            } else {
                out.value(value.format(formatter));
            }
        }

        @Override
        public LocalDateTime read(com.google.gson.stream.JsonReader in) throws java.io.IOException {
            if (in.peek() == com.google.gson.stream.JsonToken.NULL) {
                in.nextNull();
                return null;
            }
            return LocalDateTime.parse(in.nextString(), formatter);
        }
    }
}
