package com.example.demo.dto;

import lombok.Data;
import jakarta.validation.constraints.*;
import java.time.LocalDateTime;

@Data
public class RecordRequest {
    private String corr_l;
    private String corr_r;
    private String diopter_l;
    private String diopter_r;

    @NotBlank(message = "unco_l cannot be empty")
    private String unco_l;

    @NotBlank(message = "unco_r cannot be empty")
    private String unco_r;

    @NotNull(message = "Created time cannot be null")
    private LocalDateTime created_at;
}