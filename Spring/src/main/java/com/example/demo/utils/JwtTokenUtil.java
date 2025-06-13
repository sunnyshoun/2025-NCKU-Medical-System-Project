package com.example.demo.utils;

import java.util.Date;
import java.util.UUID;
import javax.crypto.SecretKey;

import org.springframework.stereotype.Component;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.security.Keys;
import io.jsonwebtoken.security.SignatureException;

@Component
public class JwtTokenUtil {

    private final static SecretKey SECRET_KEY = Keys.secretKeyFor(SignatureAlgorithm.HS256);

    private final static long ACCESS_TOKEN_EXPIRATION = 15 * 60 * 1000;     // 15 minutes
    private final static long REFRESH_TOKEN_EXPIRATION = 30L * 24 * 60 * 60 * 1000; // 30 days

    /**
     * 產生 Access Token
     */
    public String generateAccessToken(UUID userId) {
        return generateToken(userId, "access", ACCESS_TOKEN_EXPIRATION);
    }

    /**
     * 產生 Refresh Token
     */
    public String generateRefreshToken(UUID userId) {
        return generateToken(userId, "refresh", REFRESH_TOKEN_EXPIRATION);
    }

    /**
     * 核心：產生 Token（access 或 refresh）
     */
    private String generateToken(UUID userId, String tokenType, long expirationTimeMillis) {
        return Jwts.builder()
                .setSubject(userId.toString())                         // 用戶 ID
                .claim("token_type", tokenType)                        // access / refresh
                .setId(UUID.randomUUID().toString())                   // jti（JWT ID）
                .setIssuedAt(new Date())
                .setExpiration(new Date(System.currentTimeMillis() + expirationTimeMillis))
                .signWith(SECRET_KEY, SignatureAlgorithm.HS256)
                .compact();
    }

    /**
     * 驗證 Token 有效性（格式、簽名）
     */
    public boolean validateToken(String token) {
        try {
            Jwts.parserBuilder().setSigningKey(SECRET_KEY).build().parseClaimsJws(token);
            return true;
        } catch (io.jsonwebtoken.ExpiredJwtException | SignatureException |
                 io.jsonwebtoken.MalformedJwtException | IllegalArgumentException e) {
            System.err.println("JWT Validation Error: " + e.getMessage());
            return false;
        }
    }

    /**
     * 解析 user ID
     */
    public String extractUserId(String token) {
        return extractAllClaims(token).getSubject();
    }

    public UUID extractUserIdAsUUID(String token) {
        return UUID.fromString(extractUserId(token));
    }

    /**
     * 解析 jti
     */
    public String extractJti(String token) {
        return extractAllClaims(token).getId();
    }

    /**
     * 解析 token_type（access / refresh）
     */
    public String extractTokenType(String token) {
        return (String) extractAllClaims(token).get("token_type");
    }

    /**
     * 判斷是否過期
     */
    public boolean isTokenExpired(String token) {
        return extractExpiration(token).before(new Date());
    }

    private Date extractExpiration(String token) {
        return extractAllClaims(token).getExpiration();
    }

    private Claims extractAllClaims(String token) {
        return Jwts.parserBuilder()
                .setSigningKey(SECRET_KEY)
                .build()
                .parseClaimsJws(token)
                .getBody();
    }
}
