package com.example.demo.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;

/**
 * DTO for authentication response containing status and JWT token.
 */
@Data
@AllArgsConstructor
@Builder
public class AuthResponse {

    /**
     * Authentication status (e.g., "success" or "failure").
     */
    private String status;

    /**
     * JSON Web Token for authenticated user.
     */
    private String jwt;

    private String message;
}