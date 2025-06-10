package com.example.demo.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotEmpty;
import lombok.Data;

import java.util.List;

@Data
public class KnowledgeRequestWrapper {

    @NotEmpty(message = "knowledges 列表不能為空")
    @Valid
    private List<KnowledgeRequest> knowledges;
}