package com.example.demo.model;

import jakarta.persistence.*;
import lombok.Data;

import java.util.UUID;

@Entity
@Table(name = "jwt_ids")
@Data
public class JwtId {
    @Id
    @Column(name = "jti")
    private String jti;

    @Column(name = "user_id", nullable = false)
    private UUID userId;
}