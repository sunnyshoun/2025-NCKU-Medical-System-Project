package com.example.demo.dto;

import lombok.Data;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;
import java.util.Map;
import java.util.ArrayList;
import java.util.stream.Collectors;

/**
 * Grok API 回應 DTO
 * 新增支援搜索結果和引用資訊，強化引用處理功能
 */
@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class GrokResponse {
    
    /**
     * Grok 生成的回應內容
     */
    @JsonProperty("content")
    private String content;
    
    /**
     * 回應狀態
     */
    @JsonProperty("status")
    private String status;
    
    /**
     * 錯誤訊息 (如果有)
     */
    @JsonProperty("error")
    private String error;
    
    /**
     * 使用的 token 數量
     */
    @JsonProperty("tokens_used")
    private Integer tokensUsed;
    
    /**
     * 處理時間 (毫秒)
     */
    @JsonProperty("processing_time")
    private Long processingTime;
    
    /**
     * 搜索結果 (如果啟用搜索功能)
     */
    @JsonProperty("search_results")
    private List<Map<String, Object>> searchResults;
    
    /**
     * 引用資訊 (如果啟用 return_citations)
     */
    @JsonProperty("citations")
    private List<Map<String, Object>> citations;
    
    /**
     * 檢查是否有搜索結果
     */
    public boolean hasSearchResults() {
        return searchResults != null && !searchResults.isEmpty();
    }
    
    /**
     * 檢查是否有引用資訊
     */
    public boolean hasCitations() {
        return citations != null && !citations.isEmpty();
    }
    
    /**
     * 獲取引用鏈接列表（改進版本，處理各種格式）
     */
    public List<String> getCitationUrls() {
        if (!hasCitations()) {
            return new ArrayList<>();
        }
        
        return citations.stream()
                .map(citation -> {
                    Object urlObj = citation.get("url");
                    if (urlObj instanceof String) {
                        String url = ((String) urlObj).trim();
                        // 清理 URL，移除可能的特殊字符
                        url = url.replaceAll("[⁠\\s]+$", "");
                        return url.isEmpty() ? null : url;
                    }
                    return null;
                })
                .filter(url -> url != null && !url.trim().isEmpty())
                .filter(url -> url.startsWith("http://") || url.startsWith("https://"))
                .distinct()
                .collect(Collectors.toList());
    }
    
    /**
     * 獲取引用標題列表
     */
    public List<String> getCitationTitles() {
        if (!hasCitations()) {
            return new ArrayList<>();
        }
        
        return citations.stream()
                .map(citation -> {
                    Object titleObj = citation.get("title");
                    if (titleObj instanceof String) {
                        String title = ((String) titleObj).trim();
                        return title.isEmpty() ? null : title;
                    }
                    return null;
                })
                .filter(title -> title != null && !title.trim().isEmpty())
                .collect(Collectors.toList());
    }
    
    /**
     * 獲取格式化的引用資訊
     * 返回格式: "標題 - URL" 或單純 URL
     */
    public List<String> getFormattedCitations() {
        if (!hasCitations()) {
            return new ArrayList<>();
        }
        
        return citations.stream()
                .map(citation -> {
                    Object titleObj = citation.get("title");
                    Object urlObj = citation.get("url");
                    
                    String title = null;
                    String url = null;
                    
                    if (titleObj instanceof String) {
                        title = ((String) titleObj).trim();
                        if (title.isEmpty()) title = null;
                    }
                    
                    if (urlObj instanceof String) {
                        url = ((String) urlObj).trim();
                        // 清理 URL
                        url = url.replaceAll("[⁠\\s]+$", "");
                        if (url.isEmpty() || (!url.startsWith("http://") && !url.startsWith("https://"))) {
                            url = null;
                        }
                    }
                    
                    if (title != null && url != null) {
                        return title + " - " + url;
                    } else if (url != null) {
                        return url;
                    } else {
                        return null;
                    }
                })
                .filter(formatted -> formatted != null)
                .distinct()
                .collect(Collectors.toList());
    }
    
    /**
     * 獲取乾淨的 URL 列表（用於顯示）
     */
    public List<String> getCleanUrls() {
        List<String> urls = getCitationUrls();
        return urls.stream()
                .map(url -> {
                    // 如果 URL 太長，可以截斷顯示
                    if (url.length() > 80) {
                        return url.substring(0, 77) + "...";
                    }
                    return url;
                })
                .collect(Collectors.toList());
    }
    
    /**
     * 獲取引用的網域列表
     */
    public List<String> getCitationDomains() {
        return getCitationUrls().stream()
                .map(url -> {
                    try {
                        // 提取網域名稱
                        String domain = url.replaceFirst("^https?://", "")
                                          .replaceFirst("^www\\.", "")
                                          .split("/")[0];
                        return domain;
                    } catch (Exception e) {
                        return url;
                    }
                })
                .distinct()
                .collect(Collectors.toList());
    }
    
    /**
     * 檢查回應是否成功
     */
    public boolean isSuccess() {
        return "success".equals(status) && error == null;
    }
    
    /**
     * 獲取引用數量
     */
    public int getCitationCount() {
        return getCitationUrls().size();
    }
    
    /**
     * 檢查是否包含特定網域的引用
     */
    public boolean hasCitationFromDomain(String domain) {
        return getCitationDomains().stream()
                .anyMatch(citationDomain -> citationDomain.toLowerCase().contains(domain.toLowerCase()));
    }
}