package com.example.demo.model;

import jakarta.persistence.*;

@Table(name = "knowledges") // knowledges表
@Entity
public class Knowledge {

    @Id
    @Column(name = "knowledgeID", nullable = false)
    private String knowledgeId;

    @Column(name = "knowledgePoint", columnDefinition = "TEXT", nullable = false)
    private String knowledgePoint; // 知識內容

    @Column(name = "tags", columnDefinition = "TEXT[]", nullable = false)
    private String[] tags; // 知識標籤

    @Column(name = "summary", columnDefinition = "TEXT", nullable = false)
    private String summary; // 知識內容摘要

    @Column(name = "source", columnDefinition = "TEXT", nullable = false)
    private String source; // 來源網址

    public Knowledge() {
    }

    public Knowledge(String knowledgeId, String knowledgePoint, String[] tags, String summary, String source) {
        this.knowledgeId = knowledgeId;
        this.knowledgePoint = knowledgePoint;
        this.tags = tags;
        this.summary = summary;
        this.source = source;
    }

    public String getKnowledgeId() {
        return knowledgeId;
    }

    public String getKnowledgePoint() {
        return knowledgePoint;
    }

    public String[] getTags() {
        return tags;
    }

    public String getSummary() {
        return summary;
    }

    public String getSource() {
        return source;
    }
}