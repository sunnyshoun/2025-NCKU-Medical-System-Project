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
    private String access_token;
    private String refresh_token;
}