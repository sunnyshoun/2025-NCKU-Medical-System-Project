package com.example.demo.utils;

import org.springframework.util.AntPathMatcher;

import java.util.Set;

public class PathUtils {

    private static final AntPathMatcher pathMatcher = new AntPathMatcher();

    public static boolean isPublicEndpoint(String requestURI, Set<String> publicEndpoints) {
        // 規範化 requestURI，移除尾部斜槓和查詢參數
        String normalizedURI = normalizeRequestURI(requestURI);

        // 先檢查精確匹配
        if (publicEndpoints.contains(normalizedURI)) {
            return true;
        }

        // 再檢查通配符匹配，排除受保護端點
        return publicEndpoints.stream().anyMatch(pattern ->
                pathMatcher.match(pattern, normalizedURI) &&
                        !isProtectedEndpoint(normalizedURI)
        );
    }

    private static String normalizeRequestURI(String requestURI) {
        // 移除查詢參數
        if (requestURI.contains("?")) {
            requestURI = requestURI.substring(0, requestURI.indexOf("?"));
        }
        // 移除尾部斜槓
        if (requestURI.endsWith("/")) {
            requestURI = requestURI.substring(0, requestURI.length() - 1);
        }
        return requestURI;
    }

    private static boolean isProtectedEndpoint(String requestURI) {
        // 明確定義受保護的端點，防止被通配符匹配
        return requestURI.equals("/api/auth/refresh") || requestURI.equals("/api/auth/logout");
    }
}