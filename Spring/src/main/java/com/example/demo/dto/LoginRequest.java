package com.example.demo.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
@AtLeastOneNotBlank(fields = {"username", "email"}, message = "At least one of username or email must be provided")
public class LoginRequest {

    private String username;

    private String email;

    @NotBlank(message = "Password cannot be empty")
    @Size(min = 8, max = 50, message = "Password must be between 8 and 50 characters")
    private String password;
}