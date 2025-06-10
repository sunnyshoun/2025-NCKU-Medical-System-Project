package com.example.demo.dto;

import lombok.Data;

@Data
public class RegisterRequest {
    private String username;
    private String password;
    private String email;
    //選填
    private String age;
    private String gender;
    private String job;
}