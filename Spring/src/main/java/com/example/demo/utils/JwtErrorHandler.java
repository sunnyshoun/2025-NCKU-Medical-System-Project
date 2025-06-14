package com.example.demo.utils;

import com.example.demo.dto.ApiResponse;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.MalformedJwtException;
import io.jsonwebtoken.security.SecurityException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

public class JwtErrorHandler {

    public static ResponseEntity<ApiResponse<Void>> handleMissingTokenError() {
        return new ResponseEntity<>(ApiResponse.error("MISSING_TOKEN", "缺少或格式錯誤的 Authorization Header"), HttpStatus.UNAUTHORIZED);
    }

    public static ResponseEntity<ApiResponse<Void>> handleInvalidTokenTypeError() {
        return new ResponseEntity<>(ApiResponse.error("INVALID_TOKEN_TYPE", "無效的 token 類型"), HttpStatus.UNAUTHORIZED);
    }

    public static ResponseEntity<ApiResponse<Void>> handleJwtError(Exception e) {
        if (e instanceof ExpiredJwtException) {
            return new ResponseEntity<>(ApiResponse.error("TOKEN_EXPIRED", "Token 已過期"), HttpStatus.UNAUTHORIZED);
        } else if (e instanceof MalformedJwtException) {
            return new ResponseEntity<>(ApiResponse.error("INVALID_TOKEN", "無效的 Token 格式"), HttpStatus.UNAUTHORIZED);
        } else if (e instanceof SecurityException) {
            return new ResponseEntity<>(ApiResponse.error("INVALID_SIGNATURE", "Token 簽名無效"), HttpStatus.UNAUTHORIZED);
        } else if (e instanceof IllegalArgumentException) {
            return new ResponseEntity<>(ApiResponse.error("USER_NOT_FOUND", e.getMessage()), HttpStatus.UNAUTHORIZED);
        }
        return new ResponseEntity<>(ApiResponse.error("UNKNOWN_ERROR", "未知錯誤: " + e.getMessage()), HttpStatus.INTERNAL_SERVER_ERROR);
    }
}