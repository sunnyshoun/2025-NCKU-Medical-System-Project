package com.example.demo.model;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface RecordRepository extends JpaRepository<Record, Long> {

    List<Record> findByUserId(UUID userId);

    Optional<Record> findByUserIdAndRecordId(UUID userId, Long recordId);

    List<Record> findByUserIdAndCreatedAtBetween(UUID userId, LocalDateTime start, LocalDateTime end);
}