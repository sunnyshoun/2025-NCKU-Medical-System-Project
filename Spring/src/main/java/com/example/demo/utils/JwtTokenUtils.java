package com.example.demo.utils;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.security.SecureRandom;
import java.util.Date;
import java.util.UUID;

@Component
public class JwtTokenUtils {

    private final SecretKey secretKey;
    private final long accessTokenExpiration = 900000; // 15 分鐘 (900,000 毫秒)
    private final long refreshTokenExpiration = 2592000000L; // 30 天 (2,592,000,000 毫秒)

    public JwtTokenUtils() {
        this.secretKey = generateRandomKey();
    }

    private SecretKey generateRandomKey() {
        byte[] keyBytes = new byte[32];
        new SecureRandom().nextBytes(keyBytes);
        return Keys.hmacShaKeyFor(keyBytes);
    }

    private SecretKey getSigningKey() {
        return secretKey;
    }

    public String generateAccessToken(UUID userId) {
        return generateToken(userId, "access", accessTokenExpiration);
    }

    public String generateRefreshToken(UUID userId) {
        return generateToken(userId, "refresh", refreshTokenExpiration);
    }

    private String generateToken(UUID userId, String tokenType, long expirationTimeMillis) {
        return Jwts.builder()
                .setSubject(userId.toString())
                .claim("token_type", tokenType)
                .setId(UUID.randomUUID().toString())
                .setIssuedAt(new Date())
                .setExpiration(new Date(System.currentTimeMillis() + expirationTimeMillis))
                .signWith(getSigningKey(), io.jsonwebtoken.SignatureAlgorithm.HS256)
                .compact();
    }

    public Claims validateAndGetClaims(String token) {
        try {
            return Jwts.parserBuilder()
                    .setSigningKey(getSigningKey())
                    .build()
                    .parseClaimsJws(token)
                    .getBody();
        } catch (io.jsonwebtoken.ExpiredJwtException | io.jsonwebtoken.MalformedJwtException | 
                 io.jsonwebtoken.security.SecurityException | IllegalArgumentException e) {
            throw e;
        }
    }

    public String extractUserId(String token) {
        return validateAndGetClaims(token).getSubject();
    }

    public UUID extractUserIdAsUUID(String token) {
        return UUID.fromString(extractUserId(token));
    }

    public String extractJti(String token) {
        return validateAndGetClaims(token).getId();
    }

    public String extractTokenType(String token) {
        return (String) validateAndGetClaims(token).get("token_type");
    }

    public boolean isTokenExpired(String token) {
        return validateAndGetClaims(token).getExpiration().before(new Date());
    }
}