package com.example.demo.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class ChatRequest {
    @JsonProperty("content")
    @NotBlank(message = "Content cannot be empty")
    @Size(max = 300, message = "Content cannot exceed 300 characters")
    private String content;
}