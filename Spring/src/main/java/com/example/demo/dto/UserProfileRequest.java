package com.example.demo.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;

import org.hibernate.validator.constraints.Range;
import lombok.Data;

@Data
public class UserProfileRequest {
    @NotBlank(message = "username cannot be empty")
    private String username;

    @NotBlank(message = "Email cannot be empty")
    @Email(message = "Email must be valid")
    private String email;
    
    @Range(min = 1, max = 110, message = "Age must be between 1 and 110")
    private Integer age;
    
    private String gender;
    private String job;
}