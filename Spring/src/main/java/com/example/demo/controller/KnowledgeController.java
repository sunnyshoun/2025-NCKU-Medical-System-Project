package com.example.demo.controller;

import com.example.demo.annotation.JwtAuth;
import com.example.demo.dto.ApiResponse;
import com.example.demo.dto.KnowledgeRequest;
import com.example.demo.dto.KnowledgeRequestWrapper;
import com.example.demo.model.Knowledge;
import com.example.demo.repository.KnowledgeRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 知識資料管理的控制器
 */
@RestController
@RequestMapping("/api/knowledge")
public class KnowledgeController {

    @Autowired
    private KnowledgeRepository knowledgeRepository;

    @GetMapping("/{id}")
    @JwtAuth
    public ResponseEntity<ApiResponse<Knowledge>> getKnowledgeById(@PathVariable String id) {
        Knowledge knowledge = knowledgeRepository.findByKnowledgeId(id);
        if (knowledge == null) {
            return new ResponseEntity<>(ApiResponse.error("查無知識資料"), HttpStatus.NOT_FOUND);
        }
        return new ResponseEntity<>(ApiResponse.success(knowledge), HttpStatus.OK);
    }

    @PostMapping
    @Transactional
    @JwtAuth
    public ResponseEntity<ApiResponse<Void>> createKnowledge(@Valid @RequestBody KnowledgeRequestWrapper requestWrapper) {
        List<KnowledgeRequest> requests = requestWrapper.getKnowledges();

        // 檢查是否有重複的 knowledgeId
        List<String> requestIds = requests.stream()
            .map(KnowledgeRequest::getId)
            .collect(Collectors.toList());
        List<Knowledge> existingKnowledge = knowledgeRepository.findByKnowledgeIdIn(requestIds);
        if (!existingKnowledge.isEmpty()) {
            List<String> existingIds = existingKnowledge.stream()
                .map(Knowledge::getKnowledgeId)
                .collect(Collectors.toList());
            return new ResponseEntity<>(ApiResponse.error("entity error", "以下知識 ID 已存在: " + String.join(", ", existingIds)), HttpStatus.UNPROCESSABLE_ENTITY);
        }

        // 將 KnowledgeRequest 轉換為 Knowledge 物件
        List<Knowledge> knowledges = requests.stream()
            .map(req -> new Knowledge(
                req.getId(),
                req.getKnowledgePoint(),
                req.getTags(),
                req.getSummary(),
                req.getSource()
            ))
            .collect(Collectors.toList());

        // 批量儲存
        try {
            knowledgeRepository.saveAll(knowledges);
            return new ResponseEntity<>(ApiResponse.success(), HttpStatus.CREATED);
        } catch (Exception e) {
            return new ResponseEntity<>(ApiResponse.error("server error", e.getMessage()), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
}