package com.example.demo.service;

import com.example.demo.dto.GrokRequest;
import com.example.demo.dto.GrokResponse;
import com.example.demo.exception.BusinessException;
import com.example.demo.model.User.ChatMessage;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 改進的GrokService，針對眼科醫療助手進行優化
 * 新增支援搜索參數和引用鏈接功能，修正引用解析問題
 */
@Service
public class GrokService {

    @Autowired
    private RestTemplate restTemplate;

    @Value("${grok.api.key}")
    private String grokApiKey;

    @Value("${grok.api.url}")
    private String grokApiUrl;

    @Value("${grok.model:grok-3-latest}")
    private String defaultModel;

    @Value("${grok.search.enabled:false}")
    private boolean searchEnabled;

    @Value("${grok.search.mode:auto}")
    private String defaultSearchMode;

    @Value("${grok.search.return-citations:true}")
    private boolean defaultReturnCitations;

    /**
     * 搜索模式枚舉
     */
    public enum SearchMode {
        AUTO("auto"),           // 自動決定是否需要搜索
        ALWAYS("always"),       // 總是進行搜索
        NEVER("never");         // 從不搜索

        private final String value;

        SearchMode(String value) {
            this.value = value;
        }

        public String getValue() {
            return value;
        }
    }

    /**
     * 搜索參數配置類
     */
    public static class SearchParameters {
        private String mode = "auto";
        private boolean returnCitations = true;
        private String[] sources;
        private String fromDate;
        private String toDate;

        public SearchParameters() {}

        public SearchParameters(String mode, boolean returnCitations) {
            this.mode = mode;
            this.returnCitations = returnCitations;
        }

        // Builder pattern methods
        public SearchParameters mode(SearchMode mode) {
            this.mode = mode.getValue();
            return this;
        }

        public SearchParameters mode(String mode) {
            this.mode = mode;
            return this;
        }

        public SearchParameters returnCitations(boolean returnCitations) {
            this.returnCitations = returnCitations;
            return this;
        }

        public SearchParameters sources(String... sources) {
            this.sources = sources;
            return this;
        }

        public SearchParameters dateRange(String fromDate, String toDate) {
            this.fromDate = fromDate;
            this.toDate = toDate;
            return this;
        }

        // Getters
        public String getMode() { return mode; }
        public boolean isReturnCitations() { return returnCitations; }
        public String[] getSources() { return sources; }
        public String getFromDate() { return fromDate; }
        public String getToDate() { return toDate; }
    }

    /**
     * 使用完整參數配置調用 Grok API（包含搜索參數）
     */
    public GrokResponse callGrokApiWithMessages(List<ChatMessage> messages, Double temperature, 
            Integer maxTokens, SearchParameters searchParameters) {
        
        HttpHeaders headers = new HttpHeaders();
        headers.set("Authorization", "Bearer " + grokApiKey);
        headers.set("Content-Type", "application/json");

        // 構建請求體 - 針對醫療場景優化
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("model", defaultModel);
        requestBody.put("messages", messages);
        
        // 醫療回答使用較低的temperature以確保一致性和準確性
        requestBody.put("temperature", temperature != null ? temperature : 0.5);
        requestBody.put("max_tokens", maxTokens != null ? maxTokens : 500);
        
        // 添加其他有用的參數
        requestBody.put("top_p", 0.9); // 核心採樣，提高回答質量
        requestBody.put("frequency_penalty", 0.3); // 減少重複
        requestBody.put("presence_penalty", 0.1); // 鼓勵多樣性

        // 添加搜索參數（如果啟用）
        if (searchEnabled && searchParameters != null) {
            Map<String, Object> searchParams = buildSearchParametersMap(searchParameters);
            requestBody.put("search_parameters", searchParams);
        }
        HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);

        try {
            ResponseEntity<Map> response = restTemplate.exchange(
                    grokApiUrl,
                    HttpMethod.POST,
                    request,
                    Map.class
            );

            if (response.getBody() == null) {
                throw new BusinessException(
                        "GROK_API_ERROR",
                        "Grok API 回應為空",
                        HttpStatus.INTERNAL_SERVER_ERROR);
            }

            return parseGrokResponse(response.getBody());

        } catch (HttpClientErrorException e) {
            // 處理HTTP錯誤
            String errorMessage = String.format("Grok API HTTP錯誤 [%s]: %s", 
                    e.getStatusCode(), e.getResponseBodyAsString());
            throw new BusinessException(
                    "GROK_API_HTTP_ERROR",
                    errorMessage,
                    HttpStatus.INTERNAL_SERVER_ERROR
            );
        } catch (Exception e) {
            throw new BusinessException(
                    "GROK_API_ERROR",
                    "無法從 Grok API 獲取回應: " + e.getMessage(),
                    HttpStatus.INTERNAL_SERVER_ERROR
            );
        }
    }

    /**
     * 使用預設搜索參數調用 Grok API
     */
    public GrokResponse callGrokApiWithMessages(List<ChatMessage> messages, Double temperature, Integer maxTokens) {
        SearchParameters defaultSearchParams = null;
        if (searchEnabled) {
            defaultSearchParams = new SearchParameters(defaultSearchMode, defaultReturnCitations);
        }
        return callGrokApiWithMessages(messages, temperature, maxTokens, defaultSearchParams);
    }

    /**
     * 使用預設醫療場景參數調用 Grok API
     */
    public GrokResponse callGrokApiWithMessages(List<ChatMessage> messages) {
        return callGrokApiWithMessages(messages, 0.3, 1500);
    }

    /**
     * 使用搜索功能的醫療場景專用方法
     * 為醫療查詢啟用搜索以獲取最新資訊
     */
    public GrokResponse callGrokApiForMedicalQuery(List<ChatMessage> messages) {
        SearchParameters medicalSearchParams = new SearchParameters()
                .mode(SearchMode.AUTO)
                .returnCitations(true);
        
        return callGrokApiWithMessages(messages, 0.3, 1500, medicalSearchParams);
    }

    /**
     * 向後相容：使用單一提示調用 Grok API
     */
    public GrokResponse callGrokApi(String prompt) {
        List<ChatMessage> messages = List.of(new ChatMessage("user", prompt));
        return callGrokApiWithMessages(messages);
    }

    /**
     * 使用 GrokRequest 調用 API（向後相容）
     */
    public GrokResponse callGrokApi(GrokRequest grokRequest) {
        List<ChatMessage> messages = List.of(new ChatMessage("user", grokRequest.getPrompt()));
        return callGrokApiWithMessages(messages, grokRequest.getTemperature(), grokRequest.getMaxTokens());
    }

    /**
     * 構建搜索參數映射
     */
    private Map<String, Object> buildSearchParametersMap(SearchParameters searchParams) {
        Map<String, Object> searchMap = new HashMap<>();
        
        searchMap.put("mode", searchParams.getMode());
        searchMap.put("return_citations", searchParams.isReturnCitations());
        
        if (searchParams.getSources() != null && searchParams.getSources().length > 0) {
            searchMap.put("sources", searchParams.getSources());
        }
        
        if (searchParams.getFromDate() != null) {
            searchMap.put("from_date", searchParams.getFromDate());
        }
        
        if (searchParams.getToDate() != null) {
            searchMap.put("to_date", searchParams.getToDate());
        }
        
        return searchMap;
    }

    /**
     * 解析 Grok API 的回應（OpenAI 格式 + 搜索結果和引用）
     * 修正引用解析邏輯，支援多種格式
     */
    @SuppressWarnings("unchecked")
    private GrokResponse parseGrokResponse(Map<String, Object> responseBody) {
        GrokResponse grokResponse = new GrokResponse();
        System.out.println("完整回應: " + responseBody);
        
        try {
            // 檢查是否有錯誤
            if (responseBody.containsKey("error")) {
                Map<String, Object> error = (Map<String, Object>) responseBody.get("error");
                String errorMessage = (String) error.get("message");
                grokResponse.setStatus("error");
                grokResponse.setError(errorMessage);
                return grokResponse;
            }

            // 解析正常回應
            List<Map<String, Object>> choices = (List<Map<String, Object>>) responseBody.get("choices");
            if (choices != null && !choices.isEmpty()) {
                Map<String, Object> firstChoice = choices.get(0);
                Map<String, Object> message = (Map<String, Object>) firstChoice.get("message");
                if (message != null) {
                    String content = (String) message.get("content");
                    if (content != null && !content.trim().isEmpty()) {
                        grokResponse.setContent(content);
                    } else {
                        throw new BusinessException(
                                "GROK_API_EMPTY_RESPONSE",
                                "Grok API 返回空內容",
                                HttpStatus.INTERNAL_SERVER_ERROR
                        );
                    }
                }
            }

            // 解析使用資訊
            Map<String, Object> usage = (Map<String, Object>) responseBody.get("usage");
            if (usage != null) {
                grokResponse.setTokensUsed((Integer) usage.get("total_tokens"));
            }

            // 解析搜索結果（如果有）
            if (responseBody.containsKey("search_results")) {
                List<Map<String, Object>> searchResults = (List<Map<String, Object>>) responseBody.get("search_results");
                grokResponse.setSearchResults(searchResults);
            }

            // 解析引用（支援多種格式）
            if (responseBody.containsKey("citations")) {
                Object citationsObj = responseBody.get("citations");
                List<Map<String, Object>> citations = parseCitations(citationsObj);
                grokResponse.setCitations(citations);
                System.out.println("解析後的引用: " + citations);
            }

            grokResponse.setStatus("success");
            
        } catch (Exception e) {
            System.err.println("解析 Grok API 回應時發生錯誤: " + e.getMessage());
            e.printStackTrace();
            throw new BusinessException(
                    "GROK_API_PARSE_ERROR",
                    "無法解析 Grok API 回應: " + e.getMessage(),
                    HttpStatus.INTERNAL_SERVER_ERROR
            );
        }

        return grokResponse;
    }

    /**
     * 解析引用資訊，支援多種格式
     */
    @SuppressWarnings("unchecked")
    private List<Map<String, Object>> parseCitations(Object citationsObj) {
        List<Map<String, Object>> citations = new ArrayList<>();
        
        try {
            if (citationsObj instanceof List) {
                // 格式1: 物件陣列 [{"url": "...", "title": "..."}, ...]
                List<?> citationsList = (List<?>) citationsObj;
                for (Object item : citationsList) {
                    if (item instanceof Map) {
                        citations.add((Map<String, Object>) item);
                    } else if (item instanceof String) {
                        // 列表中的字串項目
                        Map<String, Object> citationMap = new HashMap<>();
                        citationMap.put("url", item.toString().trim());
                        citations.add(citationMap);
                    }
                }
            } else if (citationsObj instanceof String) {
                // 格式2: 逗號分隔的字串 "url1, url2, url3"
                String citationsStr = (String) citationsObj;
                System.out.println("原始引用字串: " + citationsStr);
                
                // 使用更精確的分割邏輯
                String[] urls = citationsStr.split(",(?=\\s*https?://)");
                
                for (String url : urls) {
                    String cleanUrl = url.trim();
                    // 移除可能的尾隨符號
                    cleanUrl = cleanUrl.replaceAll("[,，⁠\\s]+$", "");
                    
                    if (!cleanUrl.isEmpty() && (cleanUrl.startsWith("http://") || cleanUrl.startsWith("https://"))) {
                        Map<String, Object> citationMap = new HashMap<>();
                        citationMap.put("url", cleanUrl);
                        citations.add(citationMap);
                    }
                }
            } else if (citationsObj instanceof Map) {
                // 格式3: 單一物件 {"url": "...", "title": "..."}
                citations.add((Map<String, Object>) citationsObj);
            }
            
            System.out.println("解析出 " + citations.size() + " 個引用");
            for (int i = 0; i < citations.size(); i++) {
                System.out.println("引用 " + (i + 1) + ": " + citations.get(i));
            }
            
        } catch (Exception e) {
            System.err.println("解析引用時發生錯誤: " + e.getMessage());
            e.printStackTrace();
            // 如果解析失敗，回傳空列表而不是拋出異常
        }
        
        return citations;
    }

    /**
     * 創建搜索參數的便利方法
     */
    public static SearchParameters createSearchParameters() {
        return new SearchParameters();
    }

    /**
     * 創建醫療專用搜索參數
     */
    public static SearchParameters createMedicalSearchParameters() {
        return new SearchParameters()
            .mode(SearchMode.AUTO)
            .returnCitations(true)
            .sources("medical", "healthcare", "clinical");
    }

    /**
     * 創建學術搜索參數
     */
    public static SearchParameters createAcademicSearchParameters() {
        return new SearchParameters()
            .mode(SearchMode.ALWAYS)
            .returnCitations(true)
            .sources("academic", "pubmed", "scholar");
    }
}