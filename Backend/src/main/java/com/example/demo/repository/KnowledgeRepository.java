package com.example.demo.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import com.example.demo.model.Knowledge;

import java.util.List;

@Repository
public interface KnowledgeRepository extends JpaRepository<Knowledge, String> {

    Knowledge findByKnowledgeId(String knowledgeId);

    boolean existsByKnowledgeId(String knowledgeId);

    List<Knowledge> findByKnowledgeIdIn(List<String> knowledgeIds);
}