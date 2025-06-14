package com.example.demo.controller;

import com.example.demo.dto.ApiResponse;
import com.example.demo.dto.ChatRequest;
import com.example.demo.dto.ChatResponse;
import com.example.demo.exception.BusinessException;
import com.example.demo.model.User;
import com.example.demo.service.RAGService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;

/**
 * ChatController 處理 RAG 聊天功能。
 * 每個使用者同時僅有一個對話。
 * 路徑：/api/v1/chat
 */
@RestController
@RequestMapping("/api/v1/chat")
public class ChatController {

    @Autowired
    private RAGService ragService;

    /**
     * 發送聊天訊息並獲取 RAG 回應。
     * Endpoint: POST /api/v1/chat
     * 需要 JWT Token
     */
    @PostMapping
    public ResponseEntity<ApiResponse<ChatResponse>> sendMessage(@Valid @RequestBody ChatRequest chatRequest,
                                                                @AuthenticationPrincipal User currentUser) {
        ChatResponse response = ragService.processChatMessage(chatRequest.getContent(), currentUser.getId());
        return new ResponseEntity<>(ApiResponse.success(response), HttpStatus.OK);
    }

    /**
     * 刪除當前使用者的對話。
     * Endpoint: DELETE /api/v1/chat
     * 需要 JWT Token
     */
    @DeleteMapping
    public ResponseEntity<ApiResponse<Void>> deleteConversation(
            @AuthenticationPrincipal User currentUser) {
        try {
            // 刪除與當前用戶關聯的唯一對話
            ragService.deleteConversation(currentUser.getId());
            return new ResponseEntity<>(ApiResponse.success(), HttpStatus.OK);
        } catch (Exception e) {
            throw new BusinessException("CONVERSATION_NOT_FOUND", "對話不存在", HttpStatus.NOT_FOUND);
        }
    }
}