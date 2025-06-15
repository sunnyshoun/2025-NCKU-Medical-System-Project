package com.example.demo.dto;


import java.util.List;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Builder;
import lombok.Data;


@Data
@Builder
public class ChatResponse {
    
    /**
     * 回應內容
     */
    @JsonProperty("content")
    private String content;
    
    /**
     * 相關標籤
     */
    @JsonProperty("tags")
    private String[] tags;
    
    /**
     * 資訊來源描述
     */
    @JsonProperty("source")
    private List<String> source;
}