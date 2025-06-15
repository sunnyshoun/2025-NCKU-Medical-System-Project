package com.example.demo.service;

import com.example.demo.dto.ChatResponse;
import com.example.demo.dto.GrokResponse;
import com.example.demo.exception.BusinessException;
import com.example.demo.model.Knowledge;
import com.example.demo.model.Record;
import com.example.demo.model.User;
import com.example.demo.model.User.ChatMessage;
import com.example.demo.repository.KnowledgeRepository;
import com.example.demo.repository.RecordRepository;
import com.example.demo.repository.UserRepository;
import com.example.demo.vectordb.SearchRequest;
import com.example.demo.vectordb.SearchResponse;
import com.example.demo.vectordb.SearchResult;
import com.example.demo.vectordb.VectorDBServiceGrpc;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.UUID;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

/**
 * 優化的RAGService，提供更乾淨的回應格式
 */
@Service
public class RAGService {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private KnowledgeRepository knowledgeRepository;

    @Autowired
    private RecordRepository recordRepository;

    @Autowired
    private GrokService grokService;

    @Autowired
    private VectorDBServiceGrpc.VectorDBServiceBlockingStub vectorDbStub;

    @Value("${chat.context.max-messages:10}")
    private int maxContextMessages;

    @Value("${chat.vector-search.top-k:8}")
    private int vectorSearchTopK;

    @Value("${chat.vector-search.similarity-threshold:0.5}")
    private double similarityThreshold;

    private static final String OPHTHALMOLOGY_SYSTEM_PROMPT = """
        ## 角色定義
        你是一位專業的眼科醫療顧問，具備豐富的眼科知識和臨床經驗。

        ## 核心原則
        1. **安全第一**：始終強調嚴重症狀需立即就醫
        2. **專業準確**：提供基於醫學證據的資訊
        3. **簡潔回應**：針對問題核心簡潔回答，避免冗長說明
        4. **個人化建議**：結合用戶個人資料給予適切建議
        5. **衛教導向**：幫助用戶建立正確的眼科保健觀念
        7. **配合使用者語言**：請根據使用者慣用語言來回應

        ## 重要回應格式要求
        請按照以下格式提供回應，並在回應最後加上特殊標記：

        [回應內容 - 請保持簡潔自然，長度在100字內，重點回答]

        **請在回應最後務必加上以下格式的標記：**
        <<TAGS: tag1,tag2,tag3,tag4,tag5>>

        ## 回應內容要求
        1. **直接回答問題**，不要開頭說"根據知識庫"或類似表述
        2. **保持簡潔**：
           - 針對問題核心回答，不需要涵蓋所有知識點
           - 提供2-3個最重要的重點即可
           - 避免冗長的背景介紹
        3. **內容應包含**：
           - 直接回答用戶的問題
           - 關鍵的衛教建議或預防措施
           - 必要時的就醫建議
        4. **不要在內容中列出資料來源**，系統會自動處理
        5. **語調自然**，像專業醫師在簡潔解答問題，嚴禁條列出獲得的資訊

        ## 標籤生成要求
        請根據回應內容，在最後生成3-5個最相關的醫療關鍵詞標籤：
        - 標籤應為醫療相關的關鍵詞
        - 標籤要簡潔明確
        - 標籤之間用逗號分隔
        - 標籤格式：<<TAGS: 標籤1,標籤2,標籤3,標籤4,標籤5>>

        ## 自動搜索決策
        當知識庫資訊不足或需要額外資訊時，**僅搜尋以下可信賴網域**：
        #### 台灣醫療機構
        - `www.mohw.gov.tw` - 衛生福利部
        - `www.ntuh.gov.tw` - 台大醫院
        - `www.vghtpe.gov.tw` - 台北榮總
        - `www.cgh.org.tw` - 國泰醫院
        - `www.nobeleye.com.tw` - 諾貝爾眼科
        - `www.tso.org.tw` - 台灣眼科醫學會

        #### 國際權威機構
        - `www.aao.org` - 美國眼科學會
        - `www.mayoclinic.org` - 梅奧診所
        - `www.nei.nih.gov` - 美國國家眼科研究所
        - `www.hopkinsmedicine.org` - 約翰霍普金斯醫學院
        - `www.webmd.com` - WebMD
        - `www.eyecareamerica.org` - 美國眼科護理
        - `www.arvo.org` - 視覺與眼科學研究協會

        ## 緊急症狀識別
        遇到以下症狀時，**立即建議就醫**：
        - 突然視力喪失或嚴重下降
        - 劇烈眼痛伴隨噁心嘔吐
        - 眼部外傷或化學品接觸
        - 突然出現大量飛蚊症或閃光
        - 視野缺損

        ## 重要限制
        - **絕對不可編造醫學資訊**
        - **不可提供具體的診斷或治療建議**
        - **遇到緊急症狀時，必須立即建議就醫**
        - **嚴禁markdown格式(如粗體、斜體)
        - **不要將使用者的資訊和檢測紀錄直接用括號括起來放在句子中**
        - **避免回答非眼科相關問題，請婉拒使用者的提問**
        - **禁止提供檔案或程式碼給使用者**

        請根據以下資訊提供專業且簡潔易懂的回答：
        """;

    /**
     * 處理聊天訊息的簡化RAG流程
     */
    @Transactional
    public ChatResponse processChatMessage(String content, UUID userId) {
        
        // 1. 驗證使用者是否存在
        User user = getUserById(userId);

        // 2. 進行向量搜索獲取相關知識
        List<KnowledgeWithSimilarity> relevantKnowledge = searchRelevantKnowledge(content);

        // 3. 獲取用戶個人資料和病歷記錄
        List<Record> userRecords = recordRepository.findByUserId(userId);

        // 4. 構建完整的系統訊息和對話上下文
        List<ChatMessage> messages = buildMessagesWithFullContext(user, content, relevantKnowledge, userRecords);

        // 5. 使用Grok處理對話，讓它自動決定是否需要搜索
        GrokService.SearchParameters searchParams = new GrokService.SearchParameters()
                .mode(GrokService.SearchMode.AUTO)
                .returnCitations(true);
        
        GrokResponse grokResponse = grokService.callGrokApiWithMessages(messages, 0.3, 1500, searchParams);

        // 6. 更新使用者的對話歷史
        updateUserChatHistory(user, content, grokResponse.getContent());

        // 7. 構建並返回乾淨的ChatResponse
        return buildCleanChatResponse(grokResponse, relevantKnowledge);
    }

    /**
     * 搜索相關知識點
     */
    private List<KnowledgeWithSimilarity> searchRelevantKnowledge(String query) {
        SearchRequest request = SearchRequest.newBuilder()
                .setQuery(query)
                .setTopK(vectorSearchTopK)
                .build();

        try {
            SearchResponse response = vectorDbStub.searchKnowledge(request);
            
            if (!"success".equals(response.getStatus())) {
                System.err.println("VectorDB 檢索失敗: " + response.getMessage());
                return List.of();
            }

            List<String> knowledgeIds = response.getResultsList().stream()
                    .filter(result -> result.getSimilarity() >= similarityThreshold)
                    .map(SearchResult::getId)
                    .collect(Collectors.toList());

            if (knowledgeIds.isEmpty()) {
                return List.of();
            }

            List<Knowledge> knowledgeList = knowledgeRepository.findByKnowledgeIdIn(knowledgeIds);
            
            return response.getResultsList().stream()
                    .filter(result -> result.getSimilarity() >= similarityThreshold)
                    .map(result -> {
                        Knowledge knowledge = knowledgeList.stream()
                                .filter(k -> k.getKnowledgeId().equals(result.getId()))
                                .findFirst()
                                .orElse(null);
                        return knowledge != null ? 
                                new KnowledgeWithSimilarity(knowledge, result.getSimilarity()) : null;
                    })
                    .filter(Objects::nonNull)
                    .sorted((k1, k2) -> Double.compare(k2.getSimilarity(), k1.getSimilarity()))
                    .limit(5) // 最多保留5個最相關的知識點
                    .collect(Collectors.toList());
                    
        } catch (Exception e) {
            System.err.println("VectorDB 檢索錯誤: " + e.getMessage());
            return List.of();
        }
    }

    /**
     * 構建完整的對話上下文
     */
    private List<ChatMessage> buildMessagesWithFullContext(User user, String currentInput, 
            List<KnowledgeWithSimilarity> relevantKnowledge, List<Record> userRecords) {
        
        List<ChatMessage> messages = new ArrayList<>();

        // 1. 添加專業系統訊息
        String systemMessage = buildCompleteSystemMessage(user, relevantKnowledge, userRecords);
        messages.add(new ChatMessage("system", systemMessage));

        // 2. 添加歷史對話（限制數量）
        List<ChatMessage> recentMessages = user.getRecentMessages(maxContextMessages);
        messages.addAll(recentMessages);

        // 3. 添加當前使用者輸入
        messages.add(new ChatMessage("user", currentInput));

        return messages;
    }

    /**
     * 構建完整的系統訊息
     */
    private String buildCompleteSystemMessage(User user, List<KnowledgeWithSimilarity> relevantKnowledge, 
            List<Record> userRecords) {
        
        StringBuilder systemMessage = new StringBuilder(OPHTHALMOLOGY_SYSTEM_PROMPT);
        
        // 添加用戶個人資料
        systemMessage.append("\n\n## 用戶個人資料\n");
        systemMessage.append(String.format("- 年齡: %d歲\n", user.getAge() > 0 ? user.getAge() : 0));
        systemMessage.append(String.format("- 性別: %s\n", user.getGender() != null ? user.getGender() : "未提供"));
        systemMessage.append(String.format("- 職業: %s\n", user.getOccupation() != null ? user.getOccupation() : "未提供"));
        
        // 添加用戶病歷記錄
        if (!userRecords.isEmpty()) {
            systemMessage.append("\n## 用戶視力檢查記錄\n");
            for (int i = 0; i < Math.min(userRecords.size(), 3); i++) { // 最多顯示最近3次記錄
                Record record = userRecords.get(i);
                systemMessage.append(String.format("### 記錄 %d (%s)\n", i + 1, 
                        record.getCreatedAt().toLocalDate().toString()));
                systemMessage.append(String.format("- 左眼裸視: %s\n", 
                        record.getUncoL() != null ? record.getUncoL() : "未記錄"));
                systemMessage.append(String.format("- 右眼裸視: %s\n", 
                        record.getUncoR() != null ? record.getUncoR() : "未記錄"));
                if (record.getCorrL() != null) {
                    systemMessage.append(String.format("- 左眼矯正視力: %s\n", record.getCorrL()));
                }
                if (record.getCorrR() != null) {
                    systemMessage.append(String.format("- 右眼矯正視力: %s\n", record.getCorrR()));
                }
                if (record.getDiopterL() != null) {
                    systemMessage.append(String.format("- 左眼度數: %s\n", record.getDiopterL()));
                }
                if (record.getDiopterR() != null) {
                    systemMessage.append(String.format("- 右眼度數: %s\n", record.getDiopterR()));
                }
                systemMessage.append("\n");
            }
        }
        
        // 添加相關知識庫資訊
        if (!relevantKnowledge.isEmpty()) {
            systemMessage.append("\n## 相關知識庫資訊\n");
            systemMessage.append("以下是可能相關的醫療知識，請整合這些資訊來回答問題：\n\n");
            
            for (int i = 0; i < relevantKnowledge.size(); i++) {
                KnowledgeWithSimilarity kwk = relevantKnowledge.get(i);
                Knowledge knowledge = kwk.getKnowledge();
                
                systemMessage.append(String.format("### 知識點 %d\n", i + 1));
                systemMessage.append(String.format("**內容**: %s\n", knowledge.getKnowledgePoint()));
                systemMessage.append(String.format("**摘要**: %s\n", knowledge.getSummary()));
                systemMessage.append(String.format("**Similarity**: %.2f\n", kwk.getSimilarity()));
                systemMessage.append("\n");
            }
        }
        
        return systemMessage.toString();
    }

    /**
     * 構建乾淨的ChatResponse
     */
    private ChatResponse buildCleanChatResponse(GrokResponse grokResponse, List<KnowledgeWithSimilarity> relevantKnowledge) {
        
        // 解析回應內容和標籤
        ParsedResponse parsed = parseAIResponse(grokResponse.getContent());
        
        // 構建來源列表
        List<String> sources = buildSourceList(relevantKnowledge, grokResponse);
        
        return ChatResponse.builder()
                .content(parsed.getContent())
                .tags(parsed.getTags())
                .source(sources)
                .build();
    }

    /**
     * 解析AI回應，提取內容和標籤
     */
    private ParsedResponse parseAIResponse(String aiResponse) {
        // 正則表達式匹配標籤
        Pattern tagPattern = Pattern.compile("<<TAGS:\\s*([^>]+)>>");
        Matcher matcher = tagPattern.matcher(aiResponse);
        
        String content = aiResponse;
        String[] tags = new String[0];
        
        if (matcher.find()) {
            // 提取標籤
            String tagString = matcher.group(1).trim();
            tags = Arrays.stream(tagString.split(","))
                    .map(String::trim)
                    .filter(tag -> !tag.isEmpty())
                    .limit(5) // 最多5個標籤
                    .toArray(String[]::new);
            
            // 移除標籤部分，保留純內容
            content = aiResponse.replaceAll("<<TAGS:\\s*[^>]+>>", "").trim();
        }
        
        return new ParsedResponse(content, tags);
    }

    /**
     * 構建來源列表
     */
    private List<String> buildSourceList(List<KnowledgeWithSimilarity> relevantKnowledge, GrokResponse grokResponse) {
        List<String> sources = new ArrayList<>();
        
        // 收集知識庫來源
        Set<String> uniqueSources = new HashSet<>();
        for (KnowledgeWithSimilarity kwk : relevantKnowledge) {
            Knowledge knowledge = kwk.getKnowledge();
            if (knowledge.getSource() != null && !knowledge.getSource().trim().isEmpty()) {
                uniqueSources.add(knowledge.getSource().trim());
            }
        }
        
        // 添加知識庫來源
        sources.addAll(uniqueSources);
        
        // 添加網路搜索來源 URL
        if (grokResponse.hasCitations()) {
            sources.addAll(grokResponse.getCitationUrls());
        }
        
        return sources;
    }

    /**
     * 刪除使用者的對話歷史
     */
    @Transactional
    public void deleteConversation(UUID userId) {
        User user = getUserById(userId);

        if (user.getChatContext() == null || user.getChatContext().isEmpty()) {
            throw new BusinessException(
                    "CONVERSATION_NOT_FOUND",
                    "對話不存在",
                    HttpStatus.NOT_FOUND);
        }

        user.clearChatContext();
        userRepository.save(user);
    }

    /**
     * 根據ID獲取使用者
     */
    private User getUserById(UUID userId) {
        return userRepository.findById(userId)
                .orElseThrow(() -> new BusinessException(
                        "USER_NOT_FOUND",
                        "使用者不存在",
                        HttpStatus.NOT_FOUND));
    }

    /**
     * 更新使用者的對話歷史
     */
    private void updateUserChatHistory(User user, String userInput, String assistantResponse) {
        user.addUserMessage(userInput);
        user.addAssistantMessage(assistantResponse);
        
        // 控制對話歷史長度
        if (user.getChatContext().size() > maxContextMessages * 2) {
            List<ChatMessage> recentMessages = user.getRecentMessages(maxContextMessages);
            user.getChatContext().clear();
            user.getChatContext().addAll(recentMessages);
        }
        
        userRepository.save(user);
    }

    /**
     * 內部類別：帶相似度的知識點
     */
    private static class KnowledgeWithSimilarity {
        private final Knowledge knowledge;
        private final double similarity;
        
        public KnowledgeWithSimilarity(Knowledge knowledge, double similarity) {
            this.knowledge = knowledge;
            this.similarity = similarity;
        }
        
        public Knowledge getKnowledge() {
            return knowledge;
        }
        
        public double getSimilarity() {
            return similarity;
        }
    }

    /**
     * 內部類別：解析後的回應
     */
    private static class ParsedResponse {
        private final String content;
        private final String[] tags;
        
        public ParsedResponse(String content, String[] tags) {
            this.content = content;
            this.tags = tags;
        }
        
        public String getContent() {
            return content;
        }
        
        public String[] getTags() {
            return tags;
        }
    }
}