package com.example.demo.dto;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class ApiResponse<T> {
    private String status;
    private String message;
    private T data;

    // 成功回應
    public static <T> ApiResponse<T> success() {
        return ApiResponse.<T>builder()
            .status("success")
            .message("")
            .data(null)
            .build();
    }

    public static <T> ApiResponse<T> success(T data) {
        return ApiResponse.<T>builder()
            .status("success")
            .message("")
            .data(data)
            .build();
    }

    public static <T> ApiResponse<T> success(String message, T data) {
        return ApiResponse.<T>builder()
            .status("success")
            .message(message)
            .data(data)
            .build();
    }

    public static <T> ApiResponse<T> success(String status, String message, T data) {
        return ApiResponse.<T>builder()
            .status(status)
            .message(message)
            .data(data)
            .build();
    }

    // 錯誤回應
    public static <T> ApiResponse<T> error(String message) {
        return ApiResponse.<T>builder()
            .status("error")
            .message(message)
            .data(null)
            .build();
    }

    public static <T> ApiResponse<T> error(String status, String message) {
        return ApiResponse.<T>builder()
            .status(status)
            .message(message)
            .data(null)
            .build();
    }

    public static <T> ApiResponse<T> error(String status, String message, T data) {
        return ApiResponse.<T>builder()
            .status(status)
            .message(message)
            .data(data)
            .build();
    }
}