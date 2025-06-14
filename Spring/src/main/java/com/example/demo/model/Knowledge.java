package com.example.demo.model;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

@Table(name = "knowledges")
@Entity
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Knowledge {

    @Id
    @Column(name = "knowledge_id", nullable = false)
    private String knowledgeId;

    @Column(name = "knowledge_point", columnDefinition = "TEXT", nullable = false)
    private String knowledgePoint;

    @Column(name = "tags", columnDefinition = "TEXT[]", nullable = false)
    private String[] tags;

    @Column(name = "summary", columnDefinition = "TEXT", nullable = false)
    private String summary;

    @Column(name = "source", columnDefinition = "TEXT", nullable = false)
    private String source;
}