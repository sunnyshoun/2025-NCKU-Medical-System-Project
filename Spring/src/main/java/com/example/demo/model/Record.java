package com.example.demo.model;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import java.time.LocalDateTime;
import java.util.UUID;

@Table(name = "records")
@Entity
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Record {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "record_id", columnDefinition = "UUID DEFAULT gen_random_uuid()")
    private UUID recordId;

    @Column(name = "user_id", nullable = false)
    private UUID userId;

    @Column(name = "corr_l", columnDefinition = "TEXT", nullable = true)
    private String corrL;

    @Column(name = "diopter_l", columnDefinition = "TEXT", nullable = true)
    private String diopterL;

    @Column(name = "corr_r", columnDefinition = "TEXT", nullable = true)
    private String corrR;

    @Column(name = "diopter_r", columnDefinition = "TEXT", nullable = true)
    private String diopterR;

    @Column(name = "unco_l", columnDefinition = "TEXT", nullable = false)
    private String uncoL;

    @Column(name = "unco_r", columnDefinition = "TEXT", nullable = false)
    private String uncoR;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    @PrePersist
    protected void onCreate() {
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }

    @PreUpdate
    protected void onUpdate() {
        this.updatedAt = LocalDateTime.now();
    }
}