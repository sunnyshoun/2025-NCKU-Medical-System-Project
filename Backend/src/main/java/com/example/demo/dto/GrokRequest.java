package com.example.demo.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Builder;
import lombok.Data;

/**
 * Grok API 請求 DTO
 */
@Data
@Builder
public class GrokRequest {
    
    /**
     * 發送給 Grok 的提示內容
     */
    @JsonProperty("prompt")
    private String prompt;
    
    /**
     * 最大回應 token 數量 (可選)
     */
    @JsonProperty("max_tokens")
    private Integer maxTokens;
    
    /**
     * 回應的隨機性，範圍 0.0-1.0 (可選)
     */
    @JsonProperty("temperature")
    private Double temperature;
    
    /**
     * 模型名稱 (可選)
     */
    @JsonProperty("model")
    private String model;
}