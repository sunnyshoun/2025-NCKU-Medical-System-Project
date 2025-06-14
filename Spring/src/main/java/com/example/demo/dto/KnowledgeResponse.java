package com.example.demo.dto;
import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class KnowledgeResponse {
    private String id;
    private String knowledge_point;
    private String[] tags;
    private String summary;
    private String source;
}