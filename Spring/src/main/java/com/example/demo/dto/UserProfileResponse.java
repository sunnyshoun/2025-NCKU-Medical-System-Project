package com.example.demo.dto;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class UserProfileResponse {
    private String username;
    private String email;
    private Integer age;
    private String gender;
    private String job;
}