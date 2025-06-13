package com.example.demo.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;
//import java.util.UUID;

@Data
public class UserProfileRequest {
    //private UUID id;

    @NotBlank(message = "Username cannot be empty")
    private String username;

    @NotBlank(message = "Email cannot be empty")
    @Email(message = "Email must be valid")
    private String email;
    
    private String password;
    @Size(min = 8, max = 50, message = "Password must be between 8 and 50 characters")

    private String age;
    private String gender;
    private String job;

}