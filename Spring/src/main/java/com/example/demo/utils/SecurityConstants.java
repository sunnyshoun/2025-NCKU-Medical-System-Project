package com.example.demo.utils;

import java.util.Set;

public class SecurityConstants {
    public static final Set<String> PUBLIC_ENDPOINTS = Set.of(
            "/api/auth/register",
            "/api/auth/login",
            "/api/auth/verify-email"
    );
    public static final Set<String> REFRESH_TOKEN_ENDPOINTS = Set.of(
            "/api/auth/refresh",
            "/api/auth/logout"
    );
    public static final String ACCESS_TOKEN_TYPE = "access";
    public static final String REFRESH_TOKEN_TYPE = "refresh";
}