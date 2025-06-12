package com.example.demo.model;

import jakarta.persistence.*;

@Table(name = "knowledges") // 映射到資料庫的 knowledges 表
@Entity
public class Knowledge {

    @Id // <-- 標記為主鍵
    @Column(name = "knowledge_id", nullable = false) // <-- 映射到資料庫的 knowledge_id 欄位
    private String knowledgeId; // Java 屬性名為 camelCase

    @Column(name = "knowledge_point", columnDefinition = "TEXT", nullable = false) // <-- 映射到資料庫的 knowledge_point 欄位
    private String knowledgePoint; // Java 屬性名為 camelCase

    @Column(name = "tags", columnDefinition = "TEXT[]", nullable = false) // 映射到資料庫的 tags 欄位
    private String[] tags; // Java 屬性名為 camelCase

    @Column(name = "summary", columnDefinition = "TEXT", nullable = false) // 映射到資料庫的 summary 欄位
    private String summary; // Java 屬性名為 camelCase

    @Column(name = "source", columnDefinition = "TEXT", nullable = false) // 映射到資料庫的 source 欄位
    private String source; // Java 屬性名為 camelCase

    public Knowledge() {
    }

    // 構造函數參數保持 camelCase，賦值給 camelCase 屬性
    public Knowledge(String knowledgeId, String knowledgePoint, String[] tags, String summary, String source) {
        this.knowledgeId = knowledgeId;
        this.knowledgePoint = knowledgePoint;
        this.tags = tags;
        this.summary = summary;
        this.source = source;
    }

    // =========================================================
    // Getter 和 Setter 方法 (手寫確保存在，並與 camelCase 屬性名匹配)
    // =========================================================

    public String getKnowledgeId() {
        return knowledgeId;
    }

    public void setKnowledgeId(String knowledgeId) {
        this.knowledgeId = knowledgeId;
    }

    public String getKnowledgePoint() {
        return knowledgePoint;
    }

    public void setKnowledgePoint(String knowledgePoint) {
        this.knowledgePoint = knowledgePoint;
    }

    public String[] getTags() {
        return tags;
    }

    public void setTags(String[] tags) {
        this.tags = tags;
    }

    public String getSummary() {
        return summary;
    }

    public void setSummary(String summary) {
        this.summary = summary;
    }

    public String getSource() {
        return source;
    }

    public void setSource(String source) {
        this.source = source;
    }
}