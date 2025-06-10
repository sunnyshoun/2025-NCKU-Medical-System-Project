package com.example.demo.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class KnowledgeRequest {

    @NotBlank(message = "ID cannot be empty")
    private String id;

    @NotBlank(message = "Knowledge point cannot be empty")
    private String knowledgePoint;

    @NotNull(message = "Tags cannot be null")
    @Size(min = 1, message = "At least one tag is required")
    private String[] tags;

    @NotBlank(message = "Summary cannot be empty")
    private String summary;

    @NotBlank(message = "Source cannot be empty")
    private String source;
}