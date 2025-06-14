package com.example.demo.filter;

import com.example.demo.model.User;
import com.example.demo.repository.UserRepository;
import com.example.demo.utils.JwtErrorHandler;
import com.example.demo.utils.JwtTokenUtils;
import com.example.demo.utils.PathUtils;
import com.example.demo.utils.SecurityConstants;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.MalformedJwtException;
import io.jsonwebtoken.security.SecurityException;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    @Autowired
    private JwtTokenUtils jwtTokenUtils;

    @Autowired
    private UserRepository userRepository;

    // 用於序列化 ApiResponse 為 JSON
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {
        String requestURI = request.getRequestURI();

        // 檢查是否為公開端點
        if (PathUtils.isPublicEndpoint(requestURI, SecurityConstants.PUBLIC_ENDPOINTS)) {
            filterChain.doFilter(request, response);
            return;
        }

        String authHeader = request.getHeader("Authorization");

        // 檢查 Authorization 頭
        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            setErrorResponse(response, JwtErrorHandler.handleMissingTokenError());
            return;
        }

        String jwt = authHeader.substring(7);
        try {
            // 確定所需的 token 類型
            String requiredTokenType = SecurityConstants.REFRESH_TOKEN_ENDPOINTS.contains(requestURI)
                    ? SecurityConstants.REFRESH_TOKEN_TYPE
                    : SecurityConstants.ACCESS_TOKEN_TYPE;
            String tokenType = jwtTokenUtils.extractTokenType(jwt);
            // 檢查 token 類型
            if (!requiredTokenType.equals(tokenType)) {
                setErrorResponse(response, JwtErrorHandler.handleInvalidTokenTypeError());
                return;
            }

            // 驗證 token
            jwtTokenUtils.extractUserId(jwt);
            
            // 查找用戶
            User user = userRepository.findById(jwtTokenUtils.extractUserIdAsUUID(jwt))
                    .orElseThrow(() -> new IllegalArgumentException("用戶不存在"));

            // 設置 Spring Security 上下文
            if (SecurityContextHolder.getContext().getAuthentication() == null) {
                UsernamePasswordAuthenticationToken authToken = new UsernamePasswordAuthenticationToken(
                        user, null, user.getAuthorities());
                authToken.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
                SecurityContextHolder.getContext().setAuthentication(authToken);
            }

            // 設置 request attribute 以供控制器使用
            request.setAttribute("jwt_token", jwt);

            filterChain.doFilter(request, response);
        } 
        catch (ExpiredJwtException | MalformedJwtException | SecurityException | IllegalArgumentException e) {
            setErrorResponse(response, JwtErrorHandler.handleJwtError(e));
        }
    }

    private void setErrorResponse(HttpServletResponse response, ResponseEntity<?> errorResponse)
            throws IOException {
        response.setStatus(errorResponse.getStatusCode().value());
        response.setContentType("application/json; charset=UTF-8");
        response.setCharacterEncoding("UTF-8");
        // 將 ApiResponse 序列化為 JSON
        response.getWriter().write(objectMapper.writeValueAsString(errorResponse.getBody()));
    }
}