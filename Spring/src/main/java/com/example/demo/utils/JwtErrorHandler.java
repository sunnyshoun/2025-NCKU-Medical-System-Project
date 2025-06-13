package com.example.demo.utils;

import com.example.demo.dto.ApiResponse;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

public class JwtErrorHandler {

    public static ResponseEntity<ApiResponse<?>> handleJwtError(Exception e) {
        if (e instanceof io.jsonwebtoken.ExpiredJwtException) {
            return new ResponseEntity<>(ApiResponse.error("JWT token has expired"), HttpStatus.UNAUTHORIZED); // 401
        } else if (e instanceof io.jsonwebtoken.MalformedJwtException) {
            return new ResponseEntity<>(ApiResponse.error("Invalid JWT token format"), HttpStatus.BAD_REQUEST); // 400
        } else if (e instanceof io.jsonwebtoken.SignatureException) {
            return new ResponseEntity<>(ApiResponse.error("Invalid JWT token signature"), HttpStatus.BAD_REQUEST); // 400
        } else {
            return new ResponseEntity<>(ApiResponse.error("Internal server error: " + e.getMessage()), HttpStatus.INTERNAL_SERVER_ERROR); // 500
        }
    }

    public static ResponseEntity<ApiResponse<?>> handleMissingTokenError() {
        return new ResponseEntity<>(ApiResponse.error("Missing or malformed Authorization header"), HttpStatus.UNAUTHORIZED); // 401
    }

    public static ResponseEntity<ApiResponse<?>> handleInvalidTokenTypeError() {
        return new ResponseEntity<>(ApiResponse.error("Token type must be refresh"), HttpStatus.BAD_REQUEST); // 400
    }

    public static ResponseEntity<ApiResponse<?>> handleRevokedTokenError() {
        return new ResponseEntity<>(ApiResponse.error("Refresh Token does not exist or has been revoked"), HttpStatus.UNAUTHORIZED); // 401
    }
}