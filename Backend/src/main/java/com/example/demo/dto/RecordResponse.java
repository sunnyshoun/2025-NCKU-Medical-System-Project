package com.example.demo.dto;

import java.time.LocalDateTime;
import lombok.Builder;
import lombok.Data;

import java.util.UUID;

@Data
@Builder
public class RecordResponse {
    private UUID record_id;
    private UUID user_id;
    private String corr_l;
    private String corr_r;
    private String diopter_l;
    private String diopter_r;
    private String unco_l;
    private String unco_r;
    private LocalDateTime created_at;
    private LocalDateTime updated_at;
}