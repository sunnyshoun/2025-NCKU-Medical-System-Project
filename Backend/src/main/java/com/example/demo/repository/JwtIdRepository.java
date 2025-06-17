package com.example.demo.repository;

import com.example.demo.model.JwtId;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface JwtIdRepository extends JpaRepository<JwtId, String> {
    Optional<JwtId> findByJti(String jti);
    void deleteByJti(String jti);
    void deleteByUserId(UUID userId);
}