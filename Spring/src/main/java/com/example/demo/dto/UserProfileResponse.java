package com.example.demo.dto;

import lombok.Builder;
import lombok.Data;
import java.util.UUID;

@Data
@Builder
public class UserProfileResponse {
    private UUID id;
    private String username;
    private String email;
    private String age;
    private String gender;
    private String job;
}