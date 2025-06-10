package com.example.demo.dto;

import lombok.Data;

@Data
public class KnowledgeResponse {

    private String status;
    private String message;
    private String detail;

    // 成功回應
    public static KnowledgeResponse success(String message) {
        KnowledgeResponse response = new KnowledgeResponse();
        response.setStatus("success");
        response.setMessage(message);
        return response;
    }

    // 錯誤回應
    public static KnowledgeResponse error(String message, String detail) {
        KnowledgeResponse response = new KnowledgeResponse();
        response.setStatus("error");
        response.setMessage(message);
        response.setDetail(detail);
        return response;
    }
}