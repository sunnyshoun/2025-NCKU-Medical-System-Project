package com.example.demo.exception;

import com.example.demo.dto.ApiResponse;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.ConstraintViolationException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DataAccessException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.security.core.AuthenticationException;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;

import java.util.HashMap;
import java.util.Map;

@ControllerAdvice
public class GlobalExceptionHandler {
    private static final Logger logger = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    // 處理 DTO 驗證失敗
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponse<Map<String, String>>> handleValidationExceptions(MethodArgumentNotValidException ex) {
        logger.warn("Validation failed: {}", ex.getMessage());
        Map<String, String> errors = new HashMap<>();
        for (FieldError error : ex.getBindingResult().getFieldErrors()) {
            errors.put(error.getField(), error.getDefaultMessage());
        }
        return new ResponseEntity<>(
            ApiResponse.error("VALIDATION_FAILED", "驗證失敗", errors),
            HttpStatus.BAD_REQUEST
        );
    }

    // 處理自定義驗證註解
    @ExceptionHandler(ConstraintViolationException.class)
    public ResponseEntity<ApiResponse<Map<String, String>>> handleConstraintViolation(ConstraintViolationException ex) {
        logger.warn("Constraint violation: {}", ex.getMessage());
        Map<String, String> errors = new HashMap<>();
        for (ConstraintViolation<?> violation : ex.getConstraintViolations()) {
            String field = violation.getPropertyPath().toString();
            String message = violation.getMessage();
            errors.put(field, message);
        }
        return new ResponseEntity<>(
            ApiResponse.error("VALIDATION_FAILED", "驗證失敗", errors),
            HttpStatus.BAD_REQUEST
        );
    }

    // 處理無效 JSON
    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<ApiResponse<Void>> handleHttpMessageNotReadable(HttpMessageNotReadableException ex) {
        logger.warn("Invalid request body: {}", ex.getMessage());
        return new ResponseEntity<>(
            ApiResponse.error("INVALID_REQUEST_BODY", "無效的請求內容: " + ex.getMessage()),
            HttpStatus.BAD_REQUEST
        );
    }

    // 處理缺少參數
    @ExceptionHandler(MissingServletRequestParameterException.class)
    public ResponseEntity<ApiResponse<Void>> handleMissingServletRequestParameter(MissingServletRequestParameterException ex) {
        logger.warn("Missing parameter: {}", ex.getMessage());
        return new ResponseEntity<>(
            ApiResponse.error("MISSING_PARAMETER", "缺少必要的參數: " + ex.getParameterName()),
            HttpStatus.BAD_REQUEST
        );
    }

    // 處理認證失敗
    @ExceptionHandler(AuthenticationException.class)
    public ResponseEntity<ApiResponse<Void>> handleAuthenticationException(AuthenticationException ex) {
        logger.warn("Authentication failed: {}", ex.getMessage());
        return new ResponseEntity<>(
            ApiResponse.error("INVALID_CREDENTIALS", "無效的憑證"),
            HttpStatus.UNAUTHORIZED
        );
    }

    // 處理資料庫異常
    @ExceptionHandler(DataAccessException.class)
    public ResponseEntity<ApiResponse<Void>> handleDataAccessException(DataAccessException ex) {
        logger.error("Database error: {}", ex.getMessage(), ex);
        return new ResponseEntity<>(
            ApiResponse.error("DATABASE_ERROR", "資料庫錯誤: " + ex.getMessage()),
            HttpStatus.INTERNAL_SERVER_ERROR
        );
    }

    // 處理業務邏輯異常
    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<ApiResponse<Void>> handleBusinessException(BusinessException ex) {
        logger.warn("Business error: {}", ex.getMessage());
        return new ResponseEntity<>(
            ApiResponse.error(ex.getResponseStatus(),
            ex.getMessage()),
            ex.getHttpStatus()
        );
    }

    // 通用異常處理
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<Void>> handleGenericException(Exception ex) {
        logger.error("Unexpected error: {}", ex.getMessage(), ex);
        return new ResponseEntity<>(
            ApiResponse.error("UNKNOWN_ERROR", "未知錯誤: " + ex.getMessage()),
            HttpStatus.INTERNAL_SERVER_ERROR
        );
    }
}