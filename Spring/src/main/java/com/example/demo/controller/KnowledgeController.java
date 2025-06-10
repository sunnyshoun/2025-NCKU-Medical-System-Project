package com.example.demo.controller;

import com.example.demo.dto.KnowledgeRequest;
import com.example.demo.dto.KnowledgeRequestWrapper;
import com.example.demo.dto.KnowledgeResponse;
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

    /**
     * 根據 ID 取得知識資料
     * Endpoint: GET /api/knowledge/{id}
     *
     * @param id 知識資料的 ID
     * @return ResponseEntity 包含知識資料或錯誤回應
     */
    @GetMapping("/{id}")
    public ResponseEntity<?> getKnowledgeById(@PathVariable String id) {
        Knowledge knowledge = knowledgeRepository.findByKnowledgeId(id);
        if (knowledge == null) {
            return new ResponseEntity<>(KnowledgeResponse.error("知識資料不存在", "ID: " + id + " 的知識資料未找到"), HttpStatus.NOT_FOUND);
        }
        return new ResponseEntity<>(knowledge, HttpStatus.OK);
    }

    /**
     * 新增單筆或多筆知識資料
     * Endpoint: POST /api/knowledge
     *
     * @param requestWrapper 包含單筆或多筆知識資料的請求體
     * @return ResponseEntity 包含新增結果
     */
    @PostMapping
    @Transactional
    public ResponseEntity<KnowledgeResponse> createKnowledge(@Valid @RequestBody KnowledgeRequestWrapper requestWrapper) {
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
            return new ResponseEntity<>(
                KnowledgeResponse.error("無效的知識資料", "以下知識 ID 已存在: " + String.join(", ", existingIds)),
                HttpStatus.UNPROCESSABLE_ENTITY
            );
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
            return new ResponseEntity<>(KnowledgeResponse.success("知識資料新增成功"), HttpStatus.CREATED);
        } catch (Exception e) {
            return new ResponseEntity<>(
                KnowledgeResponse.error("新增知識資料時發生錯誤", e.getMessage()),
                HttpStatus.INTERNAL_SERVER_ERROR
            );
        }
    }
}