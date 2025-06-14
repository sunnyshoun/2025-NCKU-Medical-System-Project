package com.example.demo.service;

import com.example.demo.dto.ChatResponse;
import com.example.demo.exception.BusinessException;
import com.example.demo.model.Knowledge;
import com.example.demo.model.User;
import com.example.demo.repository.KnowledgeRepository;
import com.example.demo.repository.UserRepository;
import com.example.demo.vectordb.SearchRequest;
import com.example.demo.vectordb.SearchResponse;
import com.example.demo.vectordb.VectorDBServiceGrpc;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
public class RAGService {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private KnowledgeRepository knowledgeRepository;

    @Autowired
    private RestTemplate restTemplate;

    @Autowired
    private VectorDBServiceGrpc.VectorDBServiceBlockingStub vectorDbStub;

    // @Value("${grok.api.key}")
    // private String grokApiKey;

    // @Value("${grok.api.url}")
    // private String grokApiUrl;

    /**
     * 處理聊天訊息
     * @param content 使用者輸入的訊息內容
     * @param userId 當前使用者的 ID
     * @return ChatResponse 包含回應內容、標籤和來源
     */
    public ChatResponse processChatMessage(String content, UUID userId) {
        
        // 1. 查詢使用者
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new BusinessException(
                        "USER_NOT_FOUND",
                        "使用者不存在",
                        HttpStatus.NOT_FOUND));

        // 2. 獲取對話上下文
        String chatContext = user.getChatContext() != null ? user.getChatContext() : "";

        // 3. 向 VectorDB 檢索知識點 ID
        List<String> knowledgeIds = searchVectorDb(content);

        // 4. 查詢 PostgreSQL 獲取知識點
        List<Knowledge> knowledgeList = knowledgeRepository.findByKnowledgeIdIn(knowledgeIds);

        // 5. 組合提示給 Grok
        String prompt = buildPrompt(content, chatContext, knowledgeList);

        System.out.println(prompt);
        // 6. 調用 Grok API 生成回應
        // GrokResponse grokResponse = callGrokApi(prompt);

        // // 7. 更新對話上下文
        // String updatedContext = chatContext.isEmpty()
        //         ? content + "\n" + grokResponse.getContent()
        //         : chatContext + "\n" + content + "\n" + grokResponse.getContent();
        // user.setChatContext(updatedContext);
        // userRepository.save(user);

        // // 8. 構建並返回 ChatResponse
        // return ChatResponse.builder()
        //     .content(grokResponse.getContent())
        //     .tags(knowledgeList.isEmpty() ? new String[]{} : knowledgeList.get(0).getTags())
        //     .source(knowledgeList.isEmpty() ? "Grok" : knowledgeList.get(0).getSource())
        //     .build();

        return ChatResponse.builder().build();
    }

    /**
     * 刪除使用者的對話
     * @param userId 當前使用者的 ID
     */
    public void deleteConversation(UUID userId) {
        
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new BusinessException(
                        "USER_NOT_FOUND",
                        "使用者不存在",
                        HttpStatus.NOT_FOUND));

        if (user.getChatContext() == null || user.getChatContext().isEmpty()) {
            throw new BusinessException(
                    "CONVERSATION_NOT_FOUND",
                    "對話不存在",
                    HttpStatus.NOT_FOUND);
        }

        user.setChatContext(null);
        userRepository.save(user);
    }

    /**
     * 向 VectorDB 檢索知識點 ID
     * @param query 使用者輸入的查詢
     * @return 知識點 ID 列表
     */
    private List<String> searchVectorDb(String query) {
        
        SearchRequest request = SearchRequest.newBuilder()
                .setQuery(query)
                .setTopK(5)
                .build();

        try {
            SearchResponse response = vectorDbStub.searchKnowledge(request);
            if (!"success".equals(response.getStatus())) {
                throw new BusinessException(
                    "VECTOR_DB_ERROR",
                    "VectorDB 檢索失敗: " + response.getMessage(),
                    HttpStatus.INTERNAL_SERVER_ERROR
                );
            }

            List<String> knowledgeIds = response.getResultsList().stream()
                    .map(result -> result.getId())
                    .collect(Collectors.toList());
            return knowledgeIds;
        }
        catch (Exception e) {
            throw new BusinessException(
                "VECTOR_DB_ERROR",
                "無法從 VectorDB 檢索資料: " + e.getMessage(),
                HttpStatus.INTERNAL_SERVER_ERROR
            );
        }
    }

    /**
     * 構建 Grok API 的提示
     * @param content 使用者輸入
     * @param context 對話上下文
     * @param knowledgeList 知識點列表
     * @return 提示字串
     */
    private String buildPrompt(String content, String context, List<Knowledge> knowledgeList) {
        StringBuilder prompt = new StringBuilder();
        prompt.append("以下是對話上下文：\n").append(context).append("\n\n");
        prompt.append("以下是相關知識：\n");
        for (Knowledge knowledge : knowledgeList) {
            prompt.append("- 內容: ").append(knowledge.getKnowledgePoint()).append("\n");
            prompt.append("  摘要: ").append(knowledge.getSummary()).append("\n");
            prompt.append("  來源: ").append(knowledge.getSource()).append("\n");
            prompt.append("  標籤: ").append(String.join(", ", knowledge.getTags())).append("\n");
        }
        prompt.append("\n使用者輸入：\n").append(content).append("\n\n請根據上下文和知識提供簡潔且準確的回應（使用使用者的語言回應）。");
        return prompt.toString();
    }

    /**
     * 調用 Grok API
     * @param prompt 提示字串
     * @return Grok 回應
     */
    // private GrokResponse callGrokApi(String prompt) {

    //     HttpHeaders headers = new HttpHeaders();
    //     headers.set("Authorization", "Bearer " + grokApiKey);
    //     headers.set("Content-Type", "application/json");

    //     Map<String, String> requestBody = new HashMap<>();
    //     requestBody.put("prompt", prompt);

    //     HttpEntity<Map<String, String>> request = new HttpEntity<>(requestBody, headers);

    //     try {
    //         ResponseEntity<GrokResponse> response = restTemplate.exchange(
    //                 grokApiUrl,
    //                 HttpMethod.POST,
    //                 request,
    //                 GrokResponse.class
    //         );
    //         if (response.getBody() == null) {
    //             throw new BusinessException(
    //                     "GROK_API_ERROR",
    //                     "Grok API 回應為空",
    //                     HttpStatus.INTERNAL_SERVER_ERROR);
    //         }
    //         return response.getBody();
    //     }
    //     catch (Exception e) {
    //         throw new BusinessException(
    //             "GROK_API_ERROR",
    //             "無法從 Grok API 獲取回應: " + e.getMessage(),
    //             HttpStatus.INTERNAL_SERVER_ERROR
    //         );
    //     }
    // }

    // Grok API 回應類
    static class GrokResponse {
        private String content;

        public String getContent() { return content; }
        public void setContent(String content) { this.content = content; }
    }
}