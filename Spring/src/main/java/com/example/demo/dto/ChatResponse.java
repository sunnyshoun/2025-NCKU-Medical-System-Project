package com.example.demo.dto;
import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class ChatResponse {
    private String content;
    private String[] tags;
    private String source;
}